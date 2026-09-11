"""Tests for the views and for the parse_version mechanism behind them.

Two things are being checked here.

1. The holdout really is hidden. `observations_explore` and
   `observations_holdout` must between them account for every row in
   `observations_latest`, and must never both contain the same row (FR-25). If
   that ever stops being true, the owner is either studying data they are
   supposed to test on later, or silently losing rows from the charts.

2. A parser correction works the way docs/QUESTIONS.md Q1 says it does: re-read
   the ORIGINAL bronze file under the ORIGINAL received_at with
   parse_version = 2, the wrong rows stay as evidence, and
   `observations_latest` shows only the corrected values. Nothing updated,
   nothing deleted.

Everything runs against a throwaway in-memory database with synthetic rows, so
there is no network, no API key and no data/ directory involved.
"""

from datetime import date, datetime

import duckdb
import pytest

from core import paths
from db import migrations

SCHEMA = (paths.REPO_ROOT / "db" / "schema.sql").read_text()

FEED = "test_feed"
SERIES = "test_series"
ENTITY = "benchmark:brent"
BRONZE = "data/bronze/test_feed/2026-09-01T09-00-00.json"

# Two ISO weeks with known, opposite split assignments, so a test can name the
# week it expects to disappear rather than asserting something vague.
MONDAY_W36 = date(2026, 8, 31)   # we mark this one 'explore' below
MONDAY_W37 = date(2026, 9, 7)    # and this one 'holdout'

FIRST_FETCH = datetime(2026, 9, 1, 9, 0, 0)
SECOND_FETCH = datetime(2026, 9, 2, 9, 0, 0)

COLUMNS = (
    "feed_id, series_id, entity_id, period_start, period_end, value, unit, "
    "received_at, source_asof, bronze_path, parse_version"
)


@pytest.fixture
def conn():
    connection = duckdb.connect(":memory:")
    connection.execute(SCHEMA)
    connection.execute(
        "INSERT INTO split_mask VALUES ('2026-W36', 'explore'), ('2026-W37', 'holdout')"
    )
    yield connection
    connection.close()


def insert(conn, period, value, received_at=FIRST_FETCH, parse_version=1, bronze=BRONZE):
    """Add one observation row. Explicit about every column, like the real thing."""
    conn.execute(
        f"INSERT INTO observations ({COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [FEED, SERIES, ENTITY, period, period, value, "usd_per_bbl",
         received_at, None, bronze, parse_version],
    )


def values(conn, view):
    return conn.execute(
        f"SELECT period_start, value FROM {view} ORDER BY period_start"
    ).fetchall()


# --------------------------------------------------------------------------
# the holdout
# --------------------------------------------------------------------------

def test_explore_and_holdout_cover_latest_exactly_once(conn):
    """explore ∪ holdout = latest, and explore ∩ holdout = ∅ (FR-25)."""
    insert(conn, MONDAY_W36, 68.0)
    insert(conn, MONDAY_W37, 69.0)

    latest = set(values(conn, "observations_latest"))
    explore = set(values(conn, "observations_explore"))
    holdout = set(values(conn, "observations_holdout"))

    assert explore | holdout == latest
    assert explore & holdout == set()


def test_a_holdout_week_is_absent_from_explore(conn):
    """The gap in the chart is the point. 2026-W37 must simply not be there."""
    insert(conn, MONDAY_W36, 68.0)
    insert(conn, MONDAY_W37, 69.0)

    assert values(conn, "observations_explore") == [(MONDAY_W36, 68.0)]
    assert values(conn, "observations_holdout") == [(MONDAY_W37, 69.0)]


# --------------------------------------------------------------------------
# vintages
# --------------------------------------------------------------------------

def test_a_revision_appends_and_the_newest_vintage_wins(conn):
    """The source changed its mind: both numbers are kept, the newer is shown."""
    insert(conn, MONDAY_W36, 68.0, received_at=FIRST_FETCH)
    insert(conn, MONDAY_W36, 68.5, received_at=SECOND_FETCH)

    assert conn.execute("SELECT count(*) FROM observations").fetchone()[0] == 2
    assert values(conn, "observations_latest") == [(MONDAY_W36, 68.5)]


# --------------------------------------------------------------------------
# parse_version — docs/QUESTIONS.md Q1
# --------------------------------------------------------------------------

def test_a_corrected_parse_wins_and_the_wrong_rows_survive(conn):
    """The Q1 acceptance test.

    A parser bug wrote 6.8 instead of 68.0. The fix re-reads the same bronze
    file, keeps the same received_at — that really is when the data arrived —
    and writes parse_version 2. Both rows exist afterwards; only the corrected
    one is visible.
    """
    insert(conn, MONDAY_W36, 6.8, parse_version=1)    # the bug
    insert(conn, MONDAY_W36, 68.0, parse_version=2)   # the fix, same vintage

    stored = conn.execute(
        "SELECT parse_version, value FROM observations ORDER BY parse_version"
    ).fetchall()
    assert stored == [(1, 6.8), (2, 68.0)]            # the evidence is still there
    assert values(conn, "observations_latest") == [(MONDAY_W36, 68.0)]
    assert values(conn, "observations_explore") == [(MONDAY_W36, 68.0)]


def test_the_correction_does_not_leak_across_vintages(conn):
    """Highest parse_version WITHIN a vintage, then the newest vintage.

    Done the other way round — newest vintage first, then highest version — a
    corrected old vintage could outrank an uncorrected newer one. Here the
    second fetch has only a version 1, and it must still win: it is the more
    recent thing the source said.
    """
    insert(conn, MONDAY_W36, 6.8, received_at=FIRST_FETCH, parse_version=1)
    insert(conn, MONDAY_W36, 68.0, received_at=FIRST_FETCH, parse_version=2)
    insert(conn, MONDAY_W36, 70.0, received_at=SECOND_FETCH, parse_version=1)

    assert values(conn, "observations_latest") == [(MONDAY_W36, 70.0)]


def test_the_same_parse_cannot_be_stored_twice(conn):
    """parse_version is in the primary key, so re-running a re-parse is a no-op."""
    insert(conn, MONDAY_W36, 68.0, parse_version=2)
    conn.execute(
        f"INSERT OR IGNORE INTO observations ({COLUMNS}) "
        f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [FEED, SERIES, ENTITY, MONDAY_W36, MONDAY_W36, 99.0, "usd_per_bbl",
         FIRST_FETCH, None, BRONZE, 2],
    )
    assert conn.execute("SELECT count(*) FROM observations").fetchone()[0] == 1
    assert values(conn, "observations_latest") == [(MONDAY_W36, 68.0)]


def test_parse_corrections_records_why_a_file_was_read_again(conn):
    """A jump from version 1 to 2 has to be explainable in six months' time."""
    conn.execute(
        """
        INSERT INTO parse_corrections (feed_id, bronze_path, old_version, new_version, reason)
        VALUES (?, ?, 1, 2, 'decimal point: values were stored ten times too small')
        """,
        [FEED, BRONZE],
    )
    row = conn.execute(
        "SELECT feed_id, bronze_path, old_version, new_version, reason, corrected_at "
        "FROM parse_corrections"
    ).fetchone()
    assert row[2:4] == (1, 2)
    assert "decimal point" in row[4]
    assert row[5] is not None  # stamped automatically


# --------------------------------------------------------------------------
# the migration that gets an existing database to this schema
# --------------------------------------------------------------------------

OLD_OBSERVATIONS = """
CREATE TABLE observations (
    feed_id TEXT NOT NULL, series_id TEXT NOT NULL, entity_id TEXT NOT NULL,
    period_start DATE NOT NULL, period_end DATE NOT NULL, value DOUBLE,
    unit TEXT NOT NULL, received_at TIMESTAMP NOT NULL, source_asof TIMESTAMP,
    bronze_path TEXT NOT NULL,
    PRIMARY KEY (feed_id, series_id, entity_id, period_start, received_at)
);
CREATE VIEW observations_latest AS SELECT * FROM observations;
"""


def old_shape_database():
    """A database as it was before parse_version existed, with rows in it."""
    conn = duckdb.connect(":memory:")
    conn.execute(OLD_OBSERVATIONS)
    conn.execute("CREATE TABLE split_mask (iso_week TEXT PRIMARY KEY, split TEXT NOT NULL)")
    conn.execute("INSERT INTO split_mask VALUES ('2026-W36', 'explore')")
    for day, value in ((MONDAY_W36, 68.0), (date(2026, 9, 1), 68.4)):
        conn.execute(
            "INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [FEED, SERIES, ENTITY, day, day, value, "usd_per_bbl", FIRST_FETCH, None, BRONZE],
        )
    return conn


def test_migration_keeps_every_row_and_marks_it_version_one():
    conn = old_shape_database()
    before = conn.execute("SELECT count(*) FROM observations").fetchone()[0]

    migrated = migrations.add_parse_version(conn, SCHEMA)

    assert migrated == before == 2
    assert conn.execute(
        "SELECT count(*) FROM observations WHERE parse_version = 1"
    ).fetchone()[0] == 2
    assert conn.execute(
        "SELECT value FROM observations WHERE period_start = ?", [MONDAY_W36]
    ).fetchone()[0] == 68.0
    # The half-migrated table must not be left lying around.
    assert not migrations._table_exists(conn, "observations_pre_parse_version")
    conn.close()


def test_migration_is_safe_to_run_twice():
    conn = old_shape_database()
    migrations.add_parse_version(conn, SCHEMA)
    assert migrations.add_parse_version(conn, SCHEMA) == 0  # nothing left to do
    assert conn.execute("SELECT count(*) FROM observations").fetchone()[0] == 2
    conn.close()


def test_migration_does_nothing_to_a_brand_new_database():
    conn = duckdb.connect(":memory:")
    assert migrations.add_parse_version(conn, SCHEMA) == 0
    conn.close()


def test_timestamp_defaults_are_utc(conn, monkeypatch):
    """A note's noted_at must not come from the machine's local clock. Q3.

    The session is put on London time first, so that local and UTC genuinely
    differ — in a container they are usually the same and the test would pass
    without proving anything.
    """
    conn.execute("SET TimeZone='Europe/London'")
    conn.execute("INSERT INTO observation_log (note) VALUES ('brent drifted up')")

    noted_at, local_now, utc_now = conn.execute(
        "SELECT (SELECT noted_at FROM observation_log), "
        "current_localtimestamp(), timezone('UTC', now())"
    ).fetchone()
    assert abs((noted_at - utc_now).total_seconds()) < 5
    assert noted_at != local_now  # BST in September: an hour apart


def test_the_utc_default_migration_fixes_an_older_database():
    """An existing table keeps its old default until something changes it."""
    conn = duckdb.connect(":memory:")
    conn.execute(
        "CREATE TABLE observation_log (obs_id INTEGER, note TEXT, "
        "noted_at TIMESTAMP NOT NULL DEFAULT current_localtimestamp())"
    )
    assert migrations.utc_column_defaults(conn) == 1
    assert migrations.utc_column_defaults(conn) == 0  # safe to run twice

    conn.execute("SET TimeZone='Europe/London'")
    conn.execute("INSERT INTO observation_log (obs_id, note) VALUES (1, 'x')")
    noted_at, utc_now = conn.execute(
        "SELECT (SELECT noted_at FROM observation_log), timezone('UTC', now())"
    ).fetchone()
    assert abs((noted_at - utc_now).total_seconds()) < 5
    conn.close()
