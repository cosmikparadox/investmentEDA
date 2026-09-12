"""Reads the .env file once and hands out the settings it found.

There is exactly one configuration mechanism in this system: environment
variables, which .env is a file of. No config classes, no YAML, no profiles.
(CLAUDE.md forbids anything more; ARCHITECTURE.md §6 fixes the four names.)

A real environment variable beats the .env file, so a cloud session that sets
FRED_API_KEY in its own environment settings works without a .env file at all,
and nobody has to paste a key into a chat window to get it into a container.

    from core.config import settings, api_key

    settings.db_path        -> Path to the DuckDB file
    api_key("FRED_API_KEY") -> the key, or a ConfigError saying where to get one
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from core import logging as clog
from core import paths
from core.errors import ConfigError

# Where to send someone who is missing a key. Printed in the error, because the
# person reading it is usually the person who has to go and register for one.
_WHERE_TO_GET_ONE = {
    "FRED_API_KEY": "https://fredaccount.stlouisfed.org/apikey",
    "EIA_API_KEY": "https://www.eia.gov/opendata/register.php",
}


@dataclass(frozen=True)
class Settings:
    """Everything the system reads from the environment. Frozen: read-only."""

    eia_api_key: str | None
    fred_api_key: str | None
    log_level: str
    db_path: Path

    def __repr__(self) -> str:
        """Print the settings without printing the keys.

        Python shows a dataclass by listing its fields, so `print(settings)`
        would put both API keys on screen — and into whatever is recording that
        screen. This replaces them with "set" or "missing", which is the only
        thing anyone actually needs to know.
        """
        return (
            "Settings("
            f"eia_api_key={'set' if self.eia_api_key else 'missing'}, "
            f"fred_api_key={'set' if self.fred_api_key else 'missing'}, "
            f"log_level={self.log_level!r}, "
            f"db_path={str(self.db_path)!r})"
        )


def _load() -> Settings:
    """Read .env (if present) and the environment, and register the keys as secrets."""
    # override=True: .env beats a variable already set in the environment.
    # The other way round means a stale key in a cloud session's settings
    # silently wins over the one you just put in .env, and the 401 that follows
    # does not tell you that is what happened.
    load_dotenv(paths.REPO_ROOT / ".env", override=True)  # no-op if absent

    loaded = Settings(
        eia_api_key=os.environ.get("EIA_API_KEY") or None,
        fred_api_key=os.environ.get("FRED_API_KEY") or None,
        log_level=(os.environ.get("LOG_LEVEL") or "INFO").upper(),
        db_path=paths.from_repo_root(
            os.environ.get("DB_PATH") or paths.DEFAULT_DB_PATH
        ),
    )

    # Tell the logger what must never be printed, before anything can print it.
    clog.register_secret(loaded.eia_api_key)
    clog.register_secret(loaded.fred_api_key)
    clog.configure(loaded.log_level)
    return loaded


settings = _load()


def api_key(name: str) -> str:
    """Return an API key, or fail with a message saying exactly what to do.

    Missing keys are reported here, at the moment a feed actually needs one,
    rather than when this module is imported. That way the tests, `db/init.py`
    and the dashboard all run on a machine with no keys at all — which is how
    they are supposed to run, since none of them talk to a source.
    """
    value = {
        "EIA_API_KEY": settings.eia_api_key,
        "FRED_API_KEY": settings.fred_api_key,
    }.get(name, os.environ.get(name))

    if not value:
        where = _WHERE_TO_GET_ONE.get(name)
        hint = f" Free key: {where}" if where else ""
        raise ConfigError(
            f"{name} is not set. Put it in .env (copy .env.example), or set it "
            f"in your cloud session's environment variables.{hint}"
        )
    return value


def reload() -> Settings:
    """Re-read the environment. For tests that change it; not used in normal runs."""
    global settings
    settings = _load()
    return settings
