"""Where everything lives on disk. The only module that knows the layout.

Nothing else in the codebase should build a path out of "data" or "bronze" by
hand. If the layout ever changes, it changes here and nowhere else.

Every path is worked out from this file's own location, so a script behaves the
same whether you run it from the repo root, from inside db/, or from anywhere
else. (NFR-61: no absolute paths written down anywhere.)
"""

from datetime import datetime
from pathlib import Path

# core/paths.py -> core/ -> the repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = REPO_ROOT / "data"
BRONZE_DIR = DATA_DIR / "bronze"
DEFAULT_DB_PATH = DATA_DIR / "controlroom.duckdb"


def from_repo_root(path: str | Path) -> Path:
    """Turn a path written in .env into a real one.

    A relative path like `data/controlroom.duckdb` is taken to mean "relative to
    the repo root", which is what someone editing .env expects. An absolute path
    is left exactly as given.
    """
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def bronze_dir(feed_id: str) -> Path:
    """The folder holding one feed's raw files: data/bronze/<feed_id>/."""
    return BRONZE_DIR / feed_id


def bronze_path(feed_id: str, received_at: datetime) -> Path:
    """Where one fetch's raw payload goes.

    `data/bronze/<feed_id>/<received_at>.json`, as specified in PRD DR-05. The
    filename is the moment we fetched it. Windows does not allow a colon in a
    filename, so the colons in the timestamp become hyphens.
    """
    stamp = received_at.isoformat().replace(":", "-")
    return bronze_dir(feed_id) / f"{stamp}.json"


def relative_to_repo(path: str | Path) -> str:
    """Describe a path the same way on every machine.

    A file inside the repo is recorded as `data/bronze/fred/...` rather than
    `/home/someone/investmentEDA/data/bronze/fred/...`, so the value means the
    same thing to anyone who reads the database later. A file outside the repo —
    someone re-parsing an archived copy — is recorded exactly as given, because
    shortening it would be a lie.
    """
    resolved = Path(path).expanduser().resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)
