"""Records every attempt to fetch a feed, whether it worked or not.

Two functions and one small result object. An ingestor calls `start_run()`
before it does anything and `finish_run()` however it ends — success, failure or
a source that was simply unreachable. In between, the `ingest_runs` table holds
a row with status 'running', so a run that dies mid-way leaves evidence rather
than nothing.

Why this is shared code rather than something each ingestor remembers to do: a
feed that quietly stops returning data looks exactly like a feed with nothing
new to say. The run history is what tells the two apart, so it has to be written
every time, and the reliable way to make that true is to have one place that
does it. (CLAUDE.md: shared FUNCTIONS yes, shared SHAPE no. This is a function.)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import duckdb

from core.errors import BODY_CHARS, StorageError
from core.logging import get_logger, redact

log = get_logger(__name__)

Status = Literal["ok", "failed"]


@dataclass(frozen=True)
class RunResult:
    """What one run of one ingestor did. Returned by `finish_run()`.

    Frozen means it cannot be changed after it is made — a report of something
    that already happened should not be editable.
    """

    feed_id: str
    received_at: datetime
    status: Status
    rows_fetched: int       # how many rows the source gave us
    rows_inserted: int      # how many were new, after skipping ones already held
    bronze_path: str | None
    error: str | None       # redacted, first 500 characters
    duration_s: float

    def summary(self) -> str:
        """One line a human can read, for `make ingest` output and logs."""
        if self.status == "ok":
            return (
                f"{self.feed_id}: ok — {self.rows_inserted} of {self.rows_fetched} "
                f"rows new, {self.duration_s:.1f}s"
            )
        return f"{self.feed_id}: FAILED after {self.duration_s:.1f}s — {self.error}"


def start_run(
    conn: duckdb.DuckDBPyConnection,
    feed_id: str,
    received_at: datetime,
) -> int:
    """Open a run and return its `run_id`. Call this first, before fetching.

    The row is written straight away with status 'running'. If the process is
    killed before `finish_run()`, that row stays as 'running' for ever, which is
    exactly the signal you want: it says "this run started and never came back".
    """
    try:
        run_id = conn.execute(
            """
            INSERT INTO ingest_runs (feed_id, received_at, started_at, status)
            VALUES (?, ?, ?, 'running')
            RETURNING run_id
            """,
            [feed_id, received_at, datetime.now()],
        ).fetchone()[0]
    except duckdb.Error as exc:
        raise StorageError(
            feed_id,
            "could not open a run — is the database built? (uv run python db/init.py)",
            target="ingest_runs",
            cause=str(exc),
        ) from exc

    log.info("run %d started", run_id, extra={"feed": feed_id})
    return run_id


def finish_run(
    conn: duckdb.DuckDBPyConnection,
    run_id: int,
    status: Status,
    *,
    rows_fetched: int = 0,
    rows_inserted: int = 0,
    bronze_path: str | None = None,
    error: str | None = None,
) -> RunResult:
    """Close the run opened by `start_run()` and report what it did.

    Call it on every path out of an ingestor, including the failures. An error
    is trimmed to 500 characters and passed through the redactor, so an API key
    that found its way into an exception message cannot be stored here.
    """
    if status not in ("ok", "failed"):
        raise ValueError(f"status must be 'ok' or 'failed', not {status!r}")

    trimmed = redact(error)[:BODY_CHARS] if error else None
    finished_at = datetime.now()

    # An UPDATE, and the only one in the ingest path. It fills in how a run this
    # same call opened turned out; it does not change anything a source told us.
    updated = conn.execute(
        """
        UPDATE ingest_runs
        SET finished_at = ?, status = ?, rows_fetched = ?, rows_inserted = ?,
            bronze_path = ?, error = ?
        WHERE run_id = ? AND status = 'running'
        RETURNING feed_id, received_at, started_at
        """,
        [finished_at, status, rows_fetched, rows_inserted, bronze_path, trimmed, run_id],
    ).fetchall()

    if not updated:
        raise StorageError(
            "",
            f"run {run_id} is not an open run — it was never started, or it has "
            f"already been finished once",
            target="ingest_runs",
        )

    feed_id, received_at, started_at = updated[0]
    result = RunResult(
        feed_id=feed_id,
        received_at=received_at,
        status=status,
        rows_fetched=rows_fetched,
        rows_inserted=rows_inserted,
        bronze_path=bronze_path,
        error=trimmed,
        duration_s=(finished_at - started_at).total_seconds(),
    )
    log.info("%s", result.summary(), extra={"feed": feed_id})
    return result
