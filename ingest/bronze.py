"""Writes a source's reply to disk, exactly as it arrived, before anything reads it.

"Bronze" is the raw layer. A bronze file is the evidence: the bytes a source
actually sent, with nothing parsed, filtered or reformatted on the way in. It is
the cheapest insurance in the system, and it buys two things.

    A parser bug months from now is recoverable. Fix the parser, re-read the
    files already on disk, and no data is lost — see docs/QUESTIONS.md Q1 for
    how a corrected reading is stored alongside the wrong one.

    A source that changes shape, goes down, or stops serving history cannot take
    what we already have. Nobody has to ask them for it twice.

This module exists so that "write it down before you read it" is enforced by
shared code rather than by each ingestor remembering (CLAUDE.md: shared
FUNCTIONS yes, shared SHAPE no; ARCHITECTURE.md §3.3).

Two guarantees it gives that the obvious `path.write_bytes(payload)` does not:

    Atomic. The bytes go to a temporary file in the same folder and are then
    renamed into place, which on every filesystem this runs on is a single
    indivisible step. A crash halfway through leaves either no file or a
    complete one — never a truncated file that looks real.

    Never overwrites. If the path already exists, it raises rather than
    replacing it. Rule 1 says ingested data is never overwritten; a bronze file
    is the most raw form of ingested data there is.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

from core import paths
from core.errors import StorageError


def write_bronze(feed_id: str, received_at: datetime, payload: bytes) -> Path:
    """Save one fetch's raw reply and return where it went.

    `payload` is bytes, not text and not a dict, because the whole point is to
    keep what came off the wire. Turning it into a string or a dict first is
    already an interpretation.

    The filename is the fetch time: `data/bronze/<feed_id>/<received_at>.json`,
    with colons replaced by hyphens because Windows will not open a filename
    containing one (PRD DR-05).

    Raises StorageError if a file is already there — two runs at the same
    `received_at`, or a re-run of something already fetched. That is a mistake
    worth stopping for, not something to quietly write over.
    """
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError(
            f"bronze takes the raw bytes a source sent, not {type(payload).__name__}. "
            f"Encode it first, e.g. json.dumps(envelope).encode()"
        )

    path = paths.bronze_path(feed_id, received_at)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        raise StorageError(
            feed_id,
            "a bronze file for this moment already exists and will not be "
            "overwritten — use a different received_at, or re-read the existing "
            "file with read_bronze()",
            target=paths.relative_to_repo(path),
        )

    # Write to a temp file in the SAME folder, then rename. Same folder matters:
    # a rename across filesystems is a copy, and a copy is not atomic.
    handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".part")
    try:
        with os.fdopen(handle, "wb") as raw_file:
            raw_file.write(payload)
            raw_file.flush()
            os.fsync(raw_file.fileno())  # on disk, not just in the OS's buffer
        os.replace(temporary, path)      # the atomic step
    except OSError as exc:
        Path(temporary).unlink(missing_ok=True)
        raise StorageError(
            feed_id,
            "could not write the raw payload to disk",
            target=paths.relative_to_repo(path),
            cause=str(exc),
        ) from exc

    return path


def read_bronze(path: str | Path) -> bytes:
    """Read a bronze file back, byte for byte. The other half of write_bronze.

    Returns exactly what was written, with no parsing — what the caller does
    with it is the ingestor's business, and doing it here would mean this module
    knowing the shape of every feed.
    """
    file_path = Path(path)
    try:
        return file_path.read_bytes()
    except OSError as exc:
        raise StorageError(
            "",
            "could not read that bronze file",
            target=str(file_path),
            cause=str(exc),
        ) from exc
