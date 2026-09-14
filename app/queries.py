"""Every database read the app makes, in one file.

Why they are gathered here rather than spread through the pages: the app is
allowed to read exactly one view of the observations — the explore one — and
keeping the SQL in a single small file makes that easy to check by eye, and easy
to check by test (`tests/test_app_views.py` greps `app/` for the names it must
never mention).

The holdout is not hidden by the app remembering to hide it. It is hidden by the
database, in the view the app reads. There is no query here that could show it
even if someone wanted to, and there is no control in the interface that asks
for one (PRD UI-08).
"""

import sys
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import settings  # noqa: E402  (must follow the path line above)

EXPLORE = "observations_explore"


def connect() -> duckdb.DuckDBPyConnection:
    """Open the database read-only, so the app cannot damage what was collected.

    read_only is not a detail: a dashboard is the one part of this system with
    no business writing to `observations`, and saying so here means a mistake
    cannot.
    """
    if not settings.db_path.exists():
        raise FileNotFoundError(settings.db_path)
    return duckdb.connect(str(settings.db_path), read_only=True)


def series_catalogue(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Every series the app may show, with its unit, feed and freshness.

    `last_received` is our own clock — when we last had this series — not when
    the source published it.
    """
    return conn.execute(
        f"""
        SELECT o.feed_id, o.series_id, o.entity_id, o.unit,
               e.display_name AS entity_name,
               f.provider, f.upstream, f.cadence,
               max(o.received_at) AS last_received,
               min(o.period_start) AS first_period,
               max(o.period_start) AS last_period,
               count(*) AS rows_shown
        FROM {EXPLORE} o
        JOIN entity_registry e ON e.entity_id = o.entity_id
        JOIN feed_registry f ON f.feed_id = o.feed_id
        GROUP BY ALL
        ORDER BY o.feed_id, o.series_id
        """
    ).df()


def series_values(
    conn: duckdb.DuckDBPyConnection,
    series_id: str,
    since: date,
) -> pd.DataFrame:
    """One series, as the app is allowed to see it: period and value, no more."""
    return conn.execute(
        f"""
        SELECT period_start, value
        FROM {EXPLORE}
        WHERE series_id = ? AND period_start >= ?
        ORDER BY period_start
        """,
        [series_id, since],
    ).df()


def last_received(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """One row per feed: when we last heard from it and how much we hold (FR-41)."""
    return conn.execute(
        f"""
        SELECT f.feed_id, f.provider, f.cadence,
               max(o.received_at) AS last_received,
               count(*) AS rows_shown
        -- No vintage count here: the view the app reads holds one vintage of
        -- each period by construction, so it would always say 1 and would look
        -- like the history is not accumulating when it is.
        FROM feed_registry f
        LEFT JOIN {EXPLORE} o ON o.feed_id = f.feed_id
        GROUP BY ALL
        ORDER BY f.feed_id
        """
    ).df()


def recent_runs(conn: duckdb.DuckDBPyConnection, limit: int = 20) -> pd.DataFrame:
    """The last runs of every feed — the first place to look when a chart stops
    moving (ARCHITECTURE.md §5)."""
    return conn.execute(
        """
        SELECT run_id, feed_id, status, started_at, finished_at,
               rows_fetched, rows_inserted, error
        FROM ingest_runs
        ORDER BY run_id DESC
        LIMIT ?
        """,
        [limit],
    ).df()


def log_entries(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """The observation log, newest first. Read-only: the page shows, never edits."""
    return conn.execute(
        """
        SELECT obs_id, noted_at, note, series_ids, window_start, window_end,
               status, test_ref, resolved_at
        FROM observation_log
        ORDER BY noted_at DESC, obs_id DESC
        """
    ).df()


def write_note(
    note: str,
    series_ids: list[str],
    window_start: date,
    window_end: date,
) -> None:
    """Add one note to the log, with what was on screen when it was written.

    Opens its own writable connection and closes it immediately: this is the one
    thing the app writes, and the rest of it stays read-only.

    Nothing here updates or deletes. A note is a record of what someone thought
    at a moment, and a record you can edit afterwards is not evidence of anything.
    """
    conn = duckdb.connect(str(settings.db_path))
    try:
        conn.execute(
            """
            INSERT INTO observation_log (note, series_ids, window_start, window_end)
            VALUES (?, ?, ?, ?)
            """,
            [note.strip(), series_ids, window_start, window_end],
        )
    finally:
        conn.close()
