"""Tests for ingest/runs.py — the record of what ran, when, and how it went.

The point of `ingest_runs` is that a feed which quietly stops looks identical to
a feed with nothing new to say, unless every attempt is written down. So these
tests check the writing down: exactly one row per run, a status that is either
'ok' or 'failed' when it ends, an open run left visible if a process dies, and
no API key stored in an error message.
"""

from datetime import datetime

import duckdb
import pytest

from core import logging as clog, paths
from core.errors import StorageError
from ingest.runs import RunResult, finish_run, start_run

RECEIVED_AT = datetime(2026, 9, 11, 10, 0, 0)
FAKE_KEY = "abcd1234efgh5678ijkl"


@pytest.fixture
def conn():
    """A throwaway in-memory database with the real schema in it.

    In-memory means nothing is written to disk, so the tests need no data/
    directory and cannot damage the owner's database.
    """
    connection = duckdb.connect(":memory:")
    connection.execute((paths.REPO_ROOT / "db" / "schema.sql").read_text())
    yield connection
    connection.close()


def rows(conn):
    return conn.execute(
        "SELECT run_id, feed_id, status, rows_fetched, rows_inserted, "
        "bronze_path, error, started_at, finished_at FROM ingest_runs ORDER BY run_id"
    ).fetchall()


def test_a_successful_run_writes_exactly_one_row(conn):
    run_id = start_run(conn, "fred_brent_ovx", RECEIVED_AT)
    result = finish_run(
        conn, run_id, "ok", rows_fetched=12180, rows_inserted=6090,
        bronze_path="data/bronze/fred_brent_ovx/x.json",
    )

    assert len(rows(conn)) == 1
    row = rows(conn)[0]
    assert row[1:6] == ("fred_brent_ovx", "ok", 12180, 6090, "data/bronze/fred_brent_ovx/x.json")
    assert row[6] is None            # no error text on a successful run
    assert row[8] is not None        # finished_at filled in

    assert isinstance(result, RunResult)
    assert result.status == "ok"
    assert result.received_at == RECEIVED_AT
    assert result.duration_s >= 0


def test_a_failed_run_is_recorded_not_lost(conn):
    run_id = start_run(conn, "eia_crude_stocks", RECEIVED_AT)
    result = finish_run(conn, run_id, "failed", error="HTTP 503 from the EIA")

    row = rows(conn)[0]
    assert row[2] == "failed"
    assert "503" in row[6]
    assert result.rows_inserted == 0
    assert "FAILED" in result.summary()


def test_an_open_run_stays_visible_if_the_process_dies(conn):
    """No finish_run call — the row must remain, saying 'running'."""
    start_run(conn, "portwatch_hormuz", RECEIVED_AT)
    row = rows(conn)[0]
    assert row[2] == "running"
    assert row[8] is None  # finished_at still empty: it started and never came back


def test_each_run_gets_its_own_id_and_row(conn):
    first = start_run(conn, "fred_brent_ovx", RECEIVED_AT)
    finish_run(conn, first, "ok", rows_fetched=10, rows_inserted=10)
    second = start_run(conn, "fred_brent_ovx", datetime(2026, 9, 12, 10, 0, 0))
    finish_run(conn, second, "ok", rows_fetched=10, rows_inserted=0)

    assert first != second
    assert len(rows(conn)) == 2
    assert [row[4] for row in rows(conn)] == [10, 0]  # second run added nothing new


def test_a_run_cannot_be_finished_twice(conn):
    """The history of an attempt is written once. Re-closing it is a bug, loudly."""
    run_id = start_run(conn, "fred_brent_ovx", RECEIVED_AT)
    finish_run(conn, run_id, "ok")
    with pytest.raises(StorageError) as caught:
        finish_run(conn, run_id, "failed", error="second thoughts")
    assert "already been finished" in str(caught.value)


def test_finishing_a_run_that_never_started_is_an_error(conn):
    with pytest.raises(StorageError):
        finish_run(conn, 999, "ok")


def test_status_must_be_ok_or_failed(conn):
    run_id = start_run(conn, "fred_brent_ovx", RECEIVED_AT)
    with pytest.raises(ValueError):
        finish_run(conn, run_id, "nearly")


def test_an_api_key_in_an_error_is_not_stored(conn):
    """NFR-41: keys never reach logs, bronze filenames, or error text."""
    clog.register_secret(FAKE_KEY)
    run_id = start_run(conn, "fred_brent_ovx", RECEIVED_AT)
    finish_run(conn, run_id, "failed", error=f"refused: https://x.test?api_key={FAKE_KEY}")
    stored = rows(conn)[0][6]
    assert FAKE_KEY not in stored
    assert "***" in stored


def test_a_long_error_is_trimmed_to_500_characters(conn):
    run_id = start_run(conn, "fred_brent_ovx", RECEIVED_AT)
    finish_run(conn, run_id, "failed", error="x" * 5000)
    assert len(rows(conn)[0][6]) == 500


def test_starting_a_run_without_a_schema_says_so():
    """The message has to tell the owner what to run, not just fail."""
    bare = duckdb.connect(":memory:")
    with pytest.raises(StorageError) as caught:
        start_run(bare, "fred_brent_ovx", RECEIVED_AT)
    assert "db/init.py" in str(caught.value)
    bare.close()
