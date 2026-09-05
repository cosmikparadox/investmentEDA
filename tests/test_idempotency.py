"""The tests that protect rule 1: ingested data is never overwritten.

They use a small saved reply in tests/fixtures/ instead of calling FRED, so they
run offline, in a fraction of a second, and give the same answer every time. A
test that depends on a live API is a test that fails on a train.

Run them with:  uv run pytest -q
"""

import copy
import json
from datetime import datetime
from pathlib import Path

import duckdb
import pytest

from ingest import fred

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).parent / "fixtures" / "fred_envelope.json"


@pytest.fixture
def conn():
    """A fresh, empty database in memory, built from the real schema.

    In memory means it never touches data/controlroom.duckdb, so running the
    tests can never disturb data you have actually collected.
    """
    connection = duckdb.connect(":memory:")
    connection.execute((REPO_ROOT / "db" / "schema.sql").read_text())
    connection.execute(
        """
        INSERT INTO split_mask
        SELECT iso_week, split FROM read_csv(?, header = true,
               columns = {'iso_week': 'TEXT', 'split': 'TEXT'})
        """,
        [str(REPO_ROOT / "db" / "split_mask.csv")],
    )
    connection.execute((REPO_ROOT / "db" / "seed_entities.sql").read_text())
    yield connection
    connection.close()


@pytest.fixture
def envelope():
    return json.loads(FIXTURE.read_text())


def load(conn, envelope, received_at: str) -> int:
    """Parse the fixture as if it had been fetched at `received_at`, and store."""
    stamped = copy.deepcopy(envelope)
    stamped["received_at"] = received_at
    return fred.store(conn, fred.parse(stamped, FIXTURE))


# --------------------------------------------------------------------------
# Rule 1: re-running appends a vintage, it does not update or delete.
# --------------------------------------------------------------------------

def test_second_run_doubles_the_rows_and_changes_none_of_the_first(conn, envelope):
    load(conn, envelope, "2026-09-05T06:00:00")
    first = conn.execute(
        "SELECT * FROM observations ORDER BY series_id, period_start"
    ).fetchall()

    load(conn, envelope, "2026-09-06T06:00:00")  # same data, fetched a day later
    total = conn.execute("SELECT count(*) FROM observations").fetchone()[0]

    assert total == len(first) * 2, "a second run must add a full second vintage"

    still_there = conn.execute(
        """
        SELECT * FROM observations
        WHERE received_at = TIMESTAMP '2026-09-05 06:00:00'
        ORDER BY series_id, period_start
        """
    ).fetchall()
    assert still_there == first, "the first vintage must be byte-for-byte untouched"


def test_replaying_the_same_fetch_adds_nothing(conn, envelope):
    added_first = load(conn, envelope, "2026-09-05T06:00:00")
    added_again = load(conn, envelope, "2026-09-05T06:00:00")

    assert added_first > 0
    assert added_again == 0, "the same vintage twice must be a no-op, not a duplicate"


def test_both_vintages_survive_but_only_the_newest_is_shown(conn, envelope):
    load(conn, envelope, "2026-09-05T06:00:00")
    load(conn, envelope, "2026-09-06T06:00:00")

    stored = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    latest = conn.execute("SELECT count(*) FROM observations_latest").fetchone()[0]

    assert stored == 16          # 2 series x 4 days x 2 vintages
    assert latest == 8           # 2 series x 4 days, newest copy of each
    assert conn.execute(
        "SELECT DISTINCT received_at FROM observations_latest"
    ).fetchall() == [(datetime(2026, 9, 6, 6, 0),)]


# --------------------------------------------------------------------------
# Bronze is only insurance if you can actually claim on it.
# --------------------------------------------------------------------------

def test_reparsing_a_bronze_file_reproduces_identical_rows(conn, envelope, tmp_path):
    """Fix a parser bug, re-read the file you already have, get the same rows."""
    path = tmp_path / "2026-09-05T06-00-00.json"
    stamped = copy.deepcopy(envelope)
    stamped["received_at"] = "2026-09-05T06:00:00"
    path.write_text(json.dumps(stamped, indent=2))

    reloaded = fred.read_bronze(path)
    assert reloaded == stamped, "what we write is exactly what we read back"

    from_file = fred.parse(reloaded, path)
    from_memory = fred.parse(stamped, path)
    assert from_file == from_memory


def test_a_bronze_file_of_an_unknown_version_is_refused(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"feed_id": "fred_brent_ovx"}))  # no version key

    with pytest.raises(fred.BadPayload, match="version"):
        fred.read_bronze(path)


# --------------------------------------------------------------------------
# Published gaps are information, not something to drop.
# --------------------------------------------------------------------------

def test_market_holidays_are_stored_as_empty_rows_not_skipped(conn, envelope):
    load(conn, envelope, "2026-09-05T06:00:00")

    rows = conn.execute(
        """
        SELECT series_id, value FROM observations
        WHERE period_start = DATE '2026-01-01' ORDER BY series_id
        """
    ).fetchall()

    assert rows == [("brent_spot", None), ("ovx", None)], (
        "New Year's Day must exist as a row with no value"
    )


def test_the_two_series_keep_their_own_source_dates(conn, envelope):
    """FRED refreshes Brent and OVX on different days. Both must be recorded."""
    load(conn, envelope, "2026-09-05T06:00:00")

    asof = dict(conn.execute(
        "SELECT DISTINCT series_id, source_asof FROM observations ORDER BY series_id"
    ).fetchall())

    assert asof["brent_spot"] == datetime(2026, 9, 2)
    assert asof["ovx"] == datetime(2026, 9, 4)
    assert conn.execute(
        "SELECT DISTINCT received_at FROM observations"
    ).fetchall() == [(datetime(2026, 9, 5, 6, 0),)], "received_at is our clock alone"


# --------------------------------------------------------------------------
# The holdout must be a clean partition, or the whole exercise is theatre.
# --------------------------------------------------------------------------

def test_explore_and_holdout_split_the_data_with_no_overlap_and_no_loss(conn, envelope):
    load(conn, envelope, "2026-09-05T06:00:00")

    latest = conn.execute("SELECT count(*) FROM observations_latest").fetchone()[0]
    explore = conn.execute("SELECT count(*) FROM observations_explore").fetchone()[0]
    holdout = conn.execute("SELECT count(*) FROM observations_holdout").fetchone()[0]

    assert explore + holdout == latest, "every row lands in exactly one of the two"
    assert conn.execute(
        """
        SELECT count(*) FROM observations_explore e
        JOIN observations_holdout h USING (series_id, period_start)
        """
    ).fetchone()[0] == 0, "no row may appear in both"


def test_the_dashboard_view_hides_at_least_one_week_we_can_name(conn, envelope):
    """Guards against the split silently becoming a no-op."""
    load(conn, envelope, "2026-09-05T06:00:00")

    hidden = conn.execute(
        """
        SELECT DISTINCT strftime(period_start, '%G-W%V') FROM observations
        WHERE period_start NOT IN (SELECT period_start FROM observations_explore)
        """
    ).fetchall()
    assert hidden, "the fixture spans two ISO weeks; the split must remove one"


# --------------------------------------------------------------------------
# Validation: refuse a bad reply before it reaches the database.
# --------------------------------------------------------------------------

def test_a_good_reply_passes(envelope):
    fred.validate(envelope)  # must not raise


def test_a_missing_series_is_refused(envelope):
    del envelope["responses"]["OVXCLS"]
    with pytest.raises(fred.BadPayload, match="OVXCLS"):
        fred.validate(envelope)


def test_a_repeated_date_is_refused(envelope):
    body = json.loads(envelope["responses"]["DCOILBRENTEU"]["body"])
    body["observations"].append(dict(body["observations"][1]))  # 2026-01-02 twice
    envelope["responses"]["DCOILBRENTEU"]["body"] = json.dumps(body)

    with pytest.raises(fred.BadPayload, match="twice"):
        fred.validate(envelope)


def test_a_date_outside_the_window_we_asked_for_is_refused(envelope):
    body = json.loads(envelope["responses"]["OVXCLS"]["body"])
    body["observations"][0]["date"] = "1999-01-04"
    envelope["responses"]["OVXCLS"]["body"] = json.dumps(body)

    with pytest.raises(fred.BadPayload, match="outside the window"):
        fred.validate(envelope)


def test_a_value_that_is_not_a_number_is_refused(envelope):
    body = json.loads(envelope["responses"]["DCOILBRENTEU"]["body"])
    body["observations"][1]["value"] = "n/a"  # FRED's marker is '.', not this
    envelope["responses"]["DCOILBRENTEU"]["body"] = json.dumps(body)

    with pytest.raises(fred.BadPayload, match="n/a"):
        fred.validate(envelope)


def test_an_empty_series_is_refused(envelope):
    body = json.loads(envelope["responses"]["OVXCLS"]["body"])
    body["observations"] = []
    envelope["responses"]["OVXCLS"]["body"] = json.dumps(body)

    with pytest.raises(fred.BadPayload, match="zero observations"):
        fred.validate(envelope)


def test_a_negative_price_is_accepted(envelope):
    """April 2020: WTI traded below zero. Surprising is not the same as wrong."""
    body = json.loads(envelope["responses"]["DCOILBRENTEU"]["body"])
    body["observations"][1]["value"] = "-37.63"
    envelope["responses"]["DCOILBRENTEU"]["body"] = json.dumps(body)

    fred.validate(envelope)  # must not raise
