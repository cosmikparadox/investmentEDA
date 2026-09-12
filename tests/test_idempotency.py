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

from core.errors import ParseError
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


def load(conn, envelope, received_at: str, parse_version: int = 1) -> int:
    """Parse the fixture as if it had been fetched at `received_at`, and store."""
    stamped = copy.deepcopy(envelope)
    stamped["received_at"] = received_at
    return fred.store(conn, fred.parse(stamped, FIXTURE, parse_version))


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

    reloaded = fred.read_envelope(path)
    assert reloaded == stamped, "what we write is exactly what we read back"

    from_file = fred.parse(reloaded, path)
    from_memory = fred.parse(stamped, path)
    assert from_file == from_memory


def test_a_bronze_file_of_an_unknown_version_is_refused(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"feed_id": "fred_brent_ovx"}))  # no version key

    with pytest.raises(ParseError, match="version"):
        fred.read_envelope(path)


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
    with pytest.raises(ParseError, match="OVXCLS"):
        fred.validate(envelope)


def test_a_repeated_date_is_refused(envelope):
    body = json.loads(envelope["responses"]["DCOILBRENTEU"]["body"])
    body["observations"].append(dict(body["observations"][1]))  # 2026-01-02 twice
    envelope["responses"]["DCOILBRENTEU"]["body"] = json.dumps(body)

    with pytest.raises(ParseError, match="twice"):
        fred.validate(envelope)


def test_a_date_outside_the_window_we_asked_for_is_refused(envelope):
    body = json.loads(envelope["responses"]["OVXCLS"]["body"])
    body["observations"][0]["date"] = "1999-01-04"
    envelope["responses"]["OVXCLS"]["body"] = json.dumps(body)

    with pytest.raises(ParseError, match="outside the window"):
        fred.validate(envelope)


def test_a_value_that_is_not_a_number_is_refused(envelope):
    body = json.loads(envelope["responses"]["DCOILBRENTEU"]["body"])
    body["observations"][1]["value"] = "n/a"  # FRED's marker is '.', not this
    envelope["responses"]["DCOILBRENTEU"]["body"] = json.dumps(body)

    with pytest.raises(ParseError, match="n/a"):
        fred.validate(envelope)


def test_an_empty_series_is_refused(envelope):
    body = json.loads(envelope["responses"]["OVXCLS"]["body"])
    body["observations"] = []
    envelope["responses"]["OVXCLS"]["body"] = json.dumps(body)

    with pytest.raises(ParseError, match="zero observations"):
        fred.validate(envelope)


def test_a_negative_price_is_accepted(envelope):
    """April 2020: WTI traded below zero. Surprising is not the same as wrong."""
    body = json.loads(envelope["responses"]["DCOILBRENTEU"]["body"])
    body["observations"][1]["value"] = "-37.63"
    envelope["responses"]["DCOILBRENTEU"]["body"] = json.dumps(body)

    fred.validate(envelope)  # must not raise


# --------------------------------------------------------------------------
# run(): the whole ingestor, with FRED replaced by the saved fixture.
# core.http.get is the one thing tests patch (ARCHITECTURE.md §7).
# --------------------------------------------------------------------------

@pytest.fixture
def offline_fred(monkeypatch, envelope, tmp_path):
    """Answer every request from the fixture, and keep bronze in a temp folder."""
    from core import config, http
    from core import paths as core_paths
    from ingest import bronze as bronze_module

    monkeypatch.setattr(core_paths, "BRONZE_DIR", tmp_path / "bronze")
    monkeypatch.setattr(config, "settings",
                        config.Settings("eia-key", "fred-key", "INFO", tmp_path / "x.duckdb"))

    def fake_get(feed_id, url, params=None, **kwargs):
        body = envelope["responses"][params["series_id"]]["body"]
        return http.Response(status_code=200, text=body, url=url)

    monkeypatch.setattr("ingest.fred.get", fake_get)
    return bronze_module


def test_a_whole_run_records_exactly_one_ingest_run(conn, offline_fred):
    """FR-05: every run leaves a row saying what it did."""
    result = fred.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))

    assert result.status == "ok"
    assert result.rows_inserted == result.rows_fetched > 0

    runs = conn.execute(
        "SELECT feed_id, status, rows_inserted, bronze_path FROM ingest_runs"
    ).fetchall()
    assert len(runs) == 1
    assert runs[0][0:3] == ("fred_brent_ovx", "ok", result.rows_inserted)
    assert runs[0][3].endswith(".json")


def test_two_runs_double_the_rows_and_leave_two_run_records(conn, offline_fred):
    """The Week 2 milestone, at the level of the real ingestor."""
    first = fred.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))
    second = fred.run(conn, received_at=datetime(2026, 9, 13, 6, 0, 0))

    total = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    assert total == first.rows_inserted + second.rows_inserted
    assert second.rows_inserted == first.rows_inserted  # a full second vintage

    statuses = conn.execute("SELECT status FROM ingest_runs ORDER BY run_id").fetchall()
    assert statuses == [("ok",), ("ok",)]


def test_the_same_vintage_twice_inserts_nothing_but_is_still_recorded(conn, offline_fred):
    """The second attempt stored nothing — and the record says so, rather than
    the run vanishing without trace."""
    moment = datetime(2026, 9, 12, 6, 0, 0)
    fred.run(conn, received_at=moment)
    # The bronze file for that moment already exists, so the second attempt
    # cannot overwrite it: it fails loudly rather than silently re-writing.
    again = fred.run(conn, received_at=moment)

    assert again.status == "failed"
    assert "will not be overwritten" in again.error
    assert conn.execute("SELECT count(*) FROM ingest_runs").fetchone()[0] == 2


def test_a_source_failure_is_recorded_and_returned_not_raised(conn, offline_fred, monkeypatch):
    """ARCHITECTURE.md §3.1: run() never raises for a feed failure."""
    from core.errors import FeedError

    def refuse(feed_id, url, params=None, **kwargs):
        raise FeedError(feed_id, "HTTP 503", url=url, status=503, body="down for maintenance")

    monkeypatch.setattr("ingest.fred.get", refuse)
    result = fred.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))

    assert result.status == "failed"
    assert "503" in result.error
    assert conn.execute("SELECT count(*) FROM observations").fetchone()[0] == 0
    row = conn.execute("SELECT status, error FROM ingest_runs").fetchone()
    assert row[0] == "failed" and "503" in row[1]


def test_a_bad_payload_keeps_the_bronze_file(conn, offline_fred, monkeypatch, envelope):
    """FR-02/NFR-01: the raw file survives a parse failure, so it can be re-read."""
    from core import http

    def nonsense(feed_id, url, params=None, **kwargs):
        return http.Response(status_code=200, text='{"error_message": "bad request"}', url=url)

    monkeypatch.setattr("ingest.fred.get", nonsense)
    result = fred.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))

    assert result.status == "failed"
    assert result.bronze_path is not None
    assert Path(result.bronze_path).exists() or (REPO_ROOT / result.bronze_path).exists()


# --------------------------------------------------------------------------
# Replay: a parser correction, end to end. docs/QUESTIONS.md Q1.
# --------------------------------------------------------------------------

def test_a_parser_bug_is_corrected_by_re_reading_the_same_file(conn, offline_fred, monkeypatch):
    """The Q1 acceptance test, through run().

    Store a vintage with a deliberately wrong parser — every value ten times too
    small. Fix the parser, re-read the SAME bronze file at the SAME received_at,
    and the corrected rows land as parse_version 2. Both readings exist
    afterwards; the dashboard sees only the corrected one.
    """
    good_parse = fred.parse

    def buggy_parse(envelope, bronze_path, parse_version=1):
        rows = good_parse(envelope, bronze_path, parse_version)
        return [r[:5] + (None if r[5] is None else r[5] / 10,) + r[6:] for r in rows]

    monkeypatch.setattr(fred, "parse", buggy_parse)
    first = fred.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))
    assert first.status == "ok"
    bronze_file = REPO_ROOT / first.bronze_path if not Path(first.bronze_path).is_absolute() \
        else Path(first.bronze_path)

    monkeypatch.setattr(fred, "parse", good_parse)  # the fix
    corrected = fred.run(conn, bronze_path=bronze_file, reason="values were ten times too small")

    assert corrected.status == "ok"
    assert corrected.rows_inserted == first.rows_inserted

    # Both readings are stored, under one vintage.
    versions = conn.execute(
        "SELECT parse_version, count(*) FROM observations GROUP BY 1 ORDER BY 1"
    ).fetchall()
    assert versions == [(1, first.rows_inserted), (2, first.rows_inserted)]
    assert conn.execute(
        "SELECT count(DISTINCT received_at) FROM observations"
    ).fetchone()[0] == 1, "a re-read must not invent a new vintage"

    # Only the corrected values are visible.
    wrong, right = conn.execute(
        """
        SELECT
          (SELECT value FROM observations
            WHERE parse_version = 1 AND series_id = 'brent_spot'
              AND period_start = DATE '2026-01-02'),
          (SELECT value FROM observations_latest
            WHERE series_id = 'brent_spot' AND period_start = DATE '2026-01-02')
        """
    ).fetchone()
    assert right == pytest.approx(wrong * 10)

    # And the reason is on the record.
    correction = conn.execute(
        "SELECT old_version, new_version, reason FROM parse_corrections"
    ).fetchall()
    assert correction == [(1, 2, "values were ten times too small")]


def test_re_reading_an_already_corrected_file_needs_a_reason(conn, offline_fred):
    """A correction without a stated reason is a mystery waiting to happen."""
    first = fred.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))
    path = REPO_ROOT / first.bronze_path

    with pytest.raises(ValueError, match="reason"):
        fred.run(conn, bronze_path=path)


def test_replaying_a_file_never_loaded_is_a_plain_first_read(conn, offline_fred, tmp_path, envelope):
    """Rebuilding a database from bronze is not a correction: no reason needed."""
    import copy as copy_module
    stamped = copy_module.deepcopy(envelope)
    stamped["received_at"] = "2026-09-05T06:00:00"
    path = tmp_path / "2026-09-05T06-00-00.json"
    path.write_text(json.dumps(stamped, indent=2))

    result = fred.run(conn, bronze_path=path)

    assert result.status == "ok"
    assert result.received_at == datetime(2026, 9, 5, 6, 0, 0), "the file's own vintage"
    assert conn.execute(
        "SELECT DISTINCT parse_version FROM observations"
    ).fetchall() == [(1,)]
    assert conn.execute("SELECT count(*) FROM parse_corrections").fetchone()[0] == 0
