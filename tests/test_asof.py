"""Tests for queries/asof.sql — the point-in-time query (PRD FR-60).

The one that matters is `test_a_revision_is_invisible_before_it_arrived`: ask for
a date before a number was revised, and you must get the OLD number back. If that
ever stops being true, every backtest built on this database is quietly using
information from the future and will look cleverer than it was.

The query is run here exactly as a person runs it — the same file, read off
disk — with only the two settings lines replaced, so a test passing is evidence
about the real file and not about a copy of it that has drifted from it.
"""

from datetime import date, datetime

import duckdb
import pytest

from core import paths

ASOF_SQL = paths.REPO_ROOT / "queries" / "asof.sql"
MARKER = "-- ============================ QUERY ============================"

SERIES = "us_crude_stocks_ex_spr"
PERIOD = date(2026, 8, 28)

FIRST_PUBLISHED = datetime(2026, 9, 2, 6, 0, 0)    # the EIA's first number
REVISED = datetime(2026, 9, 9, 6, 0, 0)            # a week later, it changed
LATER_STILL = datetime(2026, 9, 16, 6, 0, 0)       # and changed again


def run_asof(conn, series: str, asof: datetime):
    """Run the real queries/asof.sql with our own settings.

    The file has a settings block and then a marker line; everything after the
    marker is the query. Splitting there means the test exercises the file a
    person actually edits, not a reimplementation of it.
    """
    text = ASOF_SQL.read_text()
    assert MARKER in text, "the marker line in queries/asof.sql has been removed"
    query = text.split(MARKER, 1)[1]

    conn.execute("SET VARIABLE series = ?", [series])
    conn.execute("SET VARIABLE asof_date = ?", [asof])
    return conn.execute(query).fetchall()


def insert(conn, value, received_at, parse_version=1, period=PERIOD):
    conn.execute(
        """
        INSERT INTO observations (feed_id, series_id, entity_id, period_start,
            period_end, value, unit, received_at, source_asof, bronze_path, parse_version)
        VALUES ('eia_crude_stocks', ?, 'country:USA', ?, ?, ?, 'kbbl', ?, NULL,
                'data/bronze/eia_crude_stocks/x.json', ?)
        """,
        [SERIES, period, period, value, received_at, parse_version],
    )


@pytest.fixture
def conn():
    connection = duckdb.connect(":memory:")
    connection.execute((paths.REPO_ROOT / "db" / "schema.sql").read_text())
    # One week, published once and then revised twice — what this feed really does.
    insert(connection, 411_357.0, FIRST_PUBLISHED)
    insert(connection, 412_100.0, REVISED)
    insert(connection, 412_480.0, LATER_STILL)
    yield connection
    connection.close()


# --------------------------------------------------------------------------
# The requirement: an older vintage when a later one exists.
# --------------------------------------------------------------------------

def test_a_revision_is_invisible_before_it_arrived(conn):
    """Ask on 5 September and you get the number that was on the screen then."""
    rows = run_asof(conn, SERIES, datetime(2026, 9, 5, 12, 0, 0))

    assert len(rows) == 1
    period_start, value, unit, vintage = rows[0][0], rows[0][1], rows[0][2], rows[0][3]
    assert period_start == PERIOD
    assert value == 411_357.0, "the first number, not either of the revisions"
    assert unit == "kbbl"
    assert vintage == FIRST_PUBLISHED, "and it says which vintage that was"


def test_the_same_question_answered_later_gives_the_revision(conn):
    rows = run_asof(conn, SERIES, datetime(2026, 9, 12, 12, 0, 0))
    assert [row[1] for row in rows] == [412_100.0]


def test_today_gives_the_newest_vintage(conn):
    rows = run_asof(conn, SERIES, datetime(2026, 9, 20, 12, 0, 0))
    assert [row[1] for row in rows] == [412_480.0]


def test_before_we_had_anything_the_answer_is_nothing(conn):
    """Not a zero, and not the first value we would later receive."""
    assert run_asof(conn, SERIES, datetime(2026, 8, 1, 12, 0, 0)) == []


def test_the_exact_moment_of_arrival_counts_as_known(conn):
    """received_at <= asof: a number we held at that instant was known then."""
    rows = run_asof(conn, SERIES, REVISED)
    assert [row[1] for row in rows] == [412_100.0]


def test_another_series_is_not_returned(conn):
    conn.execute(
        """
        INSERT INTO observations (feed_id, series_id, entity_id, period_start,
            period_end, value, unit, received_at, source_asof, bronze_path, parse_version)
        VALUES ('fred_brent_ovx', 'brent_spot', 'benchmark:brent', ?, ?, 68.4,
                'usd_per_bbl', ?, NULL, 'data/bronze/fred_brent_ovx/x.json', 1)
        """,
        [PERIOD, PERIOD, FIRST_PUBLISHED],
    )
    rows = run_asof(conn, "brent_spot", datetime(2026, 9, 20, 12, 0, 0))
    assert [row[1] for row in rows] == [68.4]


# --------------------------------------------------------------------------
# Parse corrections: our own misreading, not the source changing its mind.
# --------------------------------------------------------------------------

def test_a_corrected_parse_wins_within_its_vintage(conn):
    """The corrected reading of that payload is what the source told us then."""
    insert(conn, 41_135.7, datetime(2026, 9, 23, 6, 0, 0), parse_version=1)  # wrong
    insert(conn, 411_357.0, datetime(2026, 9, 23, 6, 0, 0), parse_version=2)  # fixed

    rows = run_asof(conn, SERIES, datetime(2026, 9, 24, 12, 0, 0))
    assert [row[1] for row in rows] == [411_357.0]
    assert [row[4] for row in rows] == [2], "and it says which reading that was"


# --------------------------------------------------------------------------
# This is the path that may see the holdout. That is what it is for.
# --------------------------------------------------------------------------

def test_the_holdout_is_reachable_here_and_not_from_the_app(conn):
    """FR-61: holdout queries live under queries/ and are run by hand.

    The dashboard reads a view that does not contain these weeks. This file
    reads the base table, which does — deliberately, because testing a logged
    observation is the one legitimate reason to look.
    """
    conn.execute(
        "INSERT INTO split_mask VALUES ('2026-W35', 'holdout'), ('2026-W36', 'explore')"
    )
    held_out = date(2026, 8, 26)  # 2026-W35
    insert(conn, 999.0, FIRST_PUBLISHED, period=held_out)

    from_the_app = conn.execute(
        "SELECT count(*) FROM observations_explore WHERE period_start = ?", [held_out]
    ).fetchone()[0]
    assert from_the_app == 0, "the app must not be able to see this week"

    by_hand = run_asof(conn, SERIES, datetime(2026, 9, 5, 12, 0, 0))
    assert held_out in [row[0] for row in by_hand], "but this query must"


def test_the_settings_block_still_has_both_knobs():
    """The file is meant to be edited by hand: keep the two lines findable."""
    text = ASOF_SQL.read_text()
    assert "SET VARIABLE series" in text
    assert "SET VARIABLE asof_date" in text
    assert "observations_explore" not in text, (
        "asof.sql reads the base table on purpose — see queries/README.md"
    )
