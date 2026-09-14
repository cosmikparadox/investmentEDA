"""Tests for ingest/eia.py — the feed the bitemporal design exists for.

The EIA revises published numbers and serves only the current value, so the only
record of what it said last Wednesday is the vintage we stored. These tests
check that a revision appends rather than overwrites, that a re-run is a no-op,
that every attempt is recorded, and that a change of units is refused before it
can silently redefine every stored number.

They run against a saved reply in tests/fixtures/, so there is no network, no
API key, and no data/ directory involved.
"""

import copy
import json
from datetime import datetime
from pathlib import Path

import duckdb
import pytest

from core import config, http
from core import paths as core_paths
from core.errors import ParseError
from ingest import eia

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).parent / "fixtures" / "eia_envelope.json"


@pytest.fixture
def conn():
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


@pytest.fixture
def offline_eia(monkeypatch, envelope, tmp_path):
    """Answer every request from the fixture; keep bronze in a temp folder."""
    monkeypatch.setattr(core_paths, "BRONZE_DIR", tmp_path / "bronze")
    monkeypatch.setattr(config, "settings",
                        config.Settings("eia-key", "fred-key", "INFO", tmp_path / "x.duckdb"))

    def fake_get(feed_id, url, params=None, **kwargs):
        return http.Response(200, envelope["responses"]["page_0"]["body"], url)

    monkeypatch.setattr("ingest.eia.get", fake_get)


def load(conn, envelope, received_at: str, parse_version: int = 1) -> int:
    stamped = copy.deepcopy(envelope)
    stamped["received_at"] = received_at
    return eia.store(conn, eia.parse(stamped, FIXTURE, parse_version))


def revise(envelope, period: str, new_value: str):
    """Return a copy of the fixture with one week's number changed, as the EIA does."""
    revised = copy.deepcopy(envelope)
    body = json.loads(revised["responses"]["page_0"]["body"])
    for row in body["response"]["data"]:
        if row["period"] == period:
            row["value"] = new_value
    revised["responses"]["page_0"]["body"] = json.dumps(body)
    return revised


# --------------------------------------------------------------------------
# Rule 1, and the revision this feed exists to catch.
# --------------------------------------------------------------------------

def test_a_revision_appends_and_both_numbers_survive(conn, envelope):
    """The EIA changes last week's number. We keep what it said both times."""
    load(conn, envelope, "2026-09-09T06:00:00")
    load(conn, revise(envelope, "2026-08-07", "425100"), "2026-09-16T06:00:00")

    stored = conn.execute(
        """
        SELECT received_at, value FROM observations
        WHERE period_start = DATE '2026-08-07' ORDER BY received_at
        """
    ).fetchall()
    assert [row[1] for row in stored] == [424410.0, 425100.0], (
        "both vintages of a revised week must exist"
    )

    shown = conn.execute(
        "SELECT value FROM observations_latest WHERE period_start = DATE '2026-08-07'"
    ).fetchone()[0]
    assert shown == 425100.0, "the dashboard shows the newest vintage"


def test_second_run_doubles_the_rows_and_changes_none_of_the_first(conn, envelope):
    load(conn, envelope, "2026-09-09T06:00:00")
    first = conn.execute("SELECT * FROM observations ORDER BY period_start").fetchall()

    load(conn, envelope, "2026-09-16T06:00:00")
    total = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    assert total == len(first) * 2

    still_there = conn.execute(
        """
        SELECT * FROM observations
        WHERE received_at = TIMESTAMP '2026-09-09 06:00:00' ORDER BY period_start
        """
    ).fetchall()
    assert still_there == first


def test_replaying_the_same_fetch_adds_nothing(conn, envelope):
    assert load(conn, envelope, "2026-09-09T06:00:00") == 6
    assert load(conn, envelope, "2026-09-09T06:00:00") == 0


# --------------------------------------------------------------------------
# What the rows say.
# --------------------------------------------------------------------------

def test_a_week_with_no_published_number_is_still_a_row(conn, envelope):
    load(conn, envelope, "2026-09-09T06:00:00")
    value = conn.execute(
        "SELECT value FROM observations WHERE period_start = DATE '2026-07-24'"
    ).fetchone()
    assert value == (None,), "a week the EIA did not publish is information"


def test_the_period_is_a_single_day_because_this_is_a_stock(conn, envelope):
    """Ending stocks is a level on that Friday, not a flow across the week."""
    load(conn, envelope, "2026-09-09T06:00:00")
    starts, ends = zip(*conn.execute(
        "SELECT period_start, period_end FROM observations"
    ).fetchall(), strict=True)
    assert starts == ends


def test_the_unit_is_stored_under_our_own_name(conn, envelope):
    """The EIA says MBBL, meaning thousands of barrels. We store kbbl."""
    load(conn, envelope, "2026-09-09T06:00:00")
    units = conn.execute("SELECT DISTINCT unit FROM observations").fetchall()
    assert units == [("kbbl",)]


def test_source_asof_is_null_because_the_eia_does_not_say(conn, envelope):
    load(conn, envelope, "2026-09-09T06:00:00")
    assert conn.execute(
        "SELECT DISTINCT source_asof FROM observations"
    ).fetchall() == [(None,)]


def test_the_feed_declares_its_upstream(conn, envelope):
    """Rule 2: in plain text, so two feeds from one source cannot look like
    confirmation."""
    load(conn, envelope, "2026-09-09T06:00:00")
    upstream = conn.execute(
        "SELECT upstream FROM feed_registry WHERE feed_id = ?", [eia.FEED_ID]
    ).fetchone()[0]
    assert "survey" in upstream.lower() and upstream.strip()


# --------------------------------------------------------------------------
# Validation: refuse a bad reply before it reaches the database.
# --------------------------------------------------------------------------

def test_a_good_reply_passes(envelope):
    eia.validate(envelope)


def test_a_change_of_units_is_refused(envelope):
    """The one content check: MBBL to barrels would multiply every number by 1000."""
    body = json.loads(envelope["responses"]["page_0"]["body"])
    body["response"]["data"][0]["units"] = "BBL"
    envelope["responses"]["page_0"]["body"] = json.dumps(body)

    with pytest.raises(ParseError, match="units"):
        eia.validate(envelope)


def test_a_truncated_page_run_is_refused(envelope):
    """Storing half a series would look like the series simply ends."""
    body = json.loads(envelope["responses"]["page_0"]["body"])
    body["response"]["total"] = 600  # the server says there are far more
    envelope["responses"]["page_0"]["body"] = json.dumps(body)

    with pytest.raises(ParseError, match="paging stopped early"):
        eia.validate(envelope)


def test_a_repeated_week_is_refused(envelope):
    body = json.loads(envelope["responses"]["page_0"]["body"])
    body["response"]["data"].append(dict(body["response"]["data"][0]))
    body["response"]["total"] = len(body["response"]["data"])
    envelope["responses"]["page_0"]["body"] = json.dumps(body)

    with pytest.raises(ParseError, match="twice"):
        eia.validate(envelope)


def test_an_error_reply_is_refused_not_stored(envelope):
    envelope["responses"]["page_0"]["body"] = json.dumps(
        {"error": "invalid or missing api_key"}
    )
    with pytest.raises(ParseError, match="not data"):
        eia.validate(envelope)


def test_a_big_weekly_swing_is_accepted(envelope):
    """A 20-million-barrel build is news, not a bad reading."""
    body = json.loads(envelope["responses"]["page_0"]["body"])
    body["response"]["data"][1]["value"] = "999999"
    envelope["responses"]["page_0"]["body"] = json.dumps(body)
    eia.validate(envelope)  # must not raise


# --------------------------------------------------------------------------
# run(): the whole ingestor, with the EIA replaced by the fixture.
# --------------------------------------------------------------------------

def test_a_whole_run_is_recorded(conn, offline_eia):
    result = eia.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))

    assert result.status == "ok"
    assert result.rows_inserted == 6
    row = conn.execute(
        "SELECT feed_id, status, rows_inserted FROM ingest_runs"
    ).fetchone()
    assert row == ("eia_crude_stocks", "ok", 6)


def test_a_source_failure_is_recorded_and_returned_not_raised(conn, offline_eia, monkeypatch):
    from core.errors import FeedError

    def refuse(feed_id, url, params=None, **kwargs):
        raise FeedError(feed_id, "HTTP 403", url=url, status=403, body="invalid api_key")

    monkeypatch.setattr("ingest.eia.get", refuse)
    result = eia.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))

    assert result.status == "failed" and "403" in result.error
    assert conn.execute("SELECT count(*) FROM observations").fetchone()[0] == 0
    assert conn.execute("SELECT status FROM ingest_runs").fetchone() == ("failed",)


def test_a_parser_correction_replays_the_same_file(conn, offline_eia):
    """Q1, for this feed: same vintage, next parse_version, reason recorded."""
    good_parse = eia.parse
    first = eia.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))
    path = REPO_ROOT / first.bronze_path if not Path(first.bronze_path).is_absolute() \
        else Path(first.bronze_path)

    corrected = eia.run(conn, bronze_path=path, reason="units were read as barrels")

    assert corrected.status == "ok"
    assert conn.execute(
        "SELECT count(DISTINCT received_at) FROM observations"
    ).fetchone()[0] == 1, "a re-read must not invent a vintage"
    assert conn.execute(
        "SELECT DISTINCT parse_version FROM observations ORDER BY 1"
    ).fetchall() == [(1,), (2,)]
    assert conn.execute(
        "SELECT reason FROM parse_corrections"
    ).fetchone() == ("units were read as barrels",)
    assert good_parse is eia.parse
