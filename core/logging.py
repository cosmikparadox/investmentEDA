"""One logger per module, one line per event, and no API key ever printed.

A log line looks like this:

    ts=2026-09-11T14:02:11 level=INFO module=ingest.fred feed=fred_brent_ovx
    msg="fetched 2 series"

`key=value` rather than a sentence, because it can be read by eye now and by a
script later without writing a parser.

Redaction: anything registered with `register_secret()` is replaced by `***`
wherever it appears in a log line. `core.config` registers the API keys as soon
as it loads them, so a key pasted into a URL cannot reach a log file or an error
message. (NFR-41, NFR-22.)
"""

import logging
import os
import sys

_PLACEHOLDER = "***"

# The secret values we must never print. Populated by core.config at import.
_SECRETS: set[str] = set()

_LINE = 'ts=%(asctime)s level=%(levelname)s module=%(name)s feed=%(feed)s msg="%(message)s"'
_TIME = "%Y-%m-%dT%H:%M:%S"

_configured = False


def register_secret(value: str | None) -> None:
    """Remember a value that must never appear in a log line or an error.

    Short values are ignored: a one- or two-character "secret" would blank out
    ordinary text everywhere it happened to appear.
    """
    if value and len(value) >= 8:
        _SECRETS.add(value)


def redact(text: str) -> str:
    """Replace every known secret in a piece of text with ***."""
    for secret in _SECRETS:
        text = text.replace(secret, _PLACEHOLDER)
    return text


class _RedactingFilter(logging.Filter):
    """Runs on every log record: blanks out secrets and supplies a feed name.

    A logging "filter" is the hook that gets to inspect and change a record
    before it is written. Doing redaction here means it cannot be forgotten at a
    call site — every line goes through it, including ones written by libraries.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # getMessage() applies the %s arguments first. Redacting record.msg on
        # its own is not enough: a library that logs "GET %s" with the URL as an
        # argument would have the key in record.args, untouched. httpx does
        # exactly that. Format first, redact the result, then clear the args so
        # nothing formats it a second time.
        record.msg = redact(record.getMessage())
        record.args = ()
        if not hasattr(record, "feed"):
            record.feed = "-"
        return True  # True means "keep this record"


def configure(level: str | None = None) -> None:
    """Set up logging once for the whole process.

    Safe to call repeatedly; only the first call builds anything. `level` comes
    from LOG_LEVEL in .env via core.config, and defaults to INFO.
    """
    global _configured
    resolved = (level or os.environ.get("LOG_LEVEL") or "INFO").upper()

    if not _configured:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_LINE, datefmt=_TIME))
        handler.addFilter(_RedactingFilter())
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        _configured = True

    logging.getLogger().setLevel(resolved)


class _FeedAdapter(logging.LoggerAdapter):
    """A logger that tags every line with a feed name.

    Python's stock adapter throws away any `extra=` given at the call site and
    substitutes its own, so `log.info(..., extra={"feed": "eia"})` would silently
    come out as the module's default. This one merges them, with the call site
    winning — which is what anyone writing that line expects.
    """

    def process(self, msg, kwargs):
        merged = dict(self.extra or {})
        merged.update(kwargs.get("extra") or {})
        kwargs["extra"] = merged
        return msg, kwargs


def get_logger(name: str, feed_id: str | None = None) -> logging.LoggerAdapter:
    """Return the logger for one module, optionally tagged with a feed.

    Use it as `log = get_logger(__name__, FEED_ID)` at the top of a module, then
    `log.info("...")`. The feed name is attached to every line automatically, so
    a line is traceable to a feed without repeating the name in each message.

    (A LoggerAdapter is a thin wrapper around a logger that adds fixed extra
    fields to every record it passes on.)
    """
    configure()
    return _FeedAdapter(logging.getLogger(name), {"feed": feed_id or "-"})
