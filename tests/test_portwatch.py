"""Tests for ingest/portwatch.py — daily Hormuz transit counts.

Two things get particular attention here.

The date field: the feed spec recorded epoch milliseconds and a live call
returned 'YYYY-MM-DD' strings. ArcGIS serves date-only fields either way
depending on a server setting we do not control, so both are tested — a silent
flip must not corrupt every period in the table.

Refusing to judge the numbers: transits fell from about 85 a day to single
figures during 2026. Any validation rule about plausible values would have
thrown away the most informative weeks in the series, so there is a test
asserting a collapse to zero is stored.

All offline, against tests/fixtures/portwatch_envelope.json.
"""

import copy
import json
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb
import pytest

from core import config, http
from core import paths as core_paths
from core.errors import ParseError
from ingest import portwatch

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).parent / "fixtures" / "portwatch_envelope.json"


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
def offline_portwatch(monkeypatch, envelope, tmp_path):
    monkeypatch.setattr(core_paths, "BRONZE_DIR", tmp_path / "bronze")
    monkeypatch.setattr(config, "settings",
                        config.Settings("eia-key", "fred-key", "INFO", tmp_path / "x.duckdb"))

    def fake_get(feed_id, url, params=None, **kwargs):
        return http.Response(200, envelope["responses"]["page_0"]["body"], url)

    monkeypatch.setattr("ingest.portwatch.get", fake_get)


def load(conn, envelope, received_at: str, parse_version: int = 1) -> int:
    stamped = copy.deepcopy(envelope)
    stamped["received_at"] = received_at
    return portwatch.store(conn, portwatch.parse(stamped, FIXTURE, parse_version))


def edit_features(envelope, change):
    """Return a copy of the fixture with `change` applied to its features list."""
    edited = copy.deepcopy(envelope)
    body = json.loads(edited["responses"]["page_0"]["body"])
    change(body["features"])
    edited["responses"]["page_0"]["body"] = json.dumps(body)
    return edited


# --------------------------------------------------------------------------
# The date field, in both shapes the server might send.
# --------------------------------------------------------------------------

def test_a_date_string_is_read_as_a_date():
    assert portwatch.to_date("2026-08-24") == date(2026, 8, 24)


def test_epoch_milliseconds_are_read_as_the_same_date():
    """The shape the feed spec recorded. UTC, because their day boundary is."""
    midnight = datetime(2026, 8, 24, tzinfo=UTC).timestamp() * 1000
    assert portwatch.to_date(midnight) == date(2026, 8, 24)


def test_a_date_of_an_unexpected_type_is_refused():
    with pytest.raises(ValueError, match="expected"):
        portwatch.to_date({"not": "a date"})


def test_both_date_shapes_produce_identical_rows(conn, envelope):
    """A server-side flip between the two must not change a single stored row."""
    as_strings = portwatch.parse(envelope, FIXTURE)

    as_epoch = edit_features(envelope, lambda feats: [
        f["attributes"].update(
            date=datetime.fromisoformat(f["attributes"]["date"])
                 .replace(tzinfo=UTC).timestamp() * 1000
        ) for f in feats
    ])
    assert portwatch.parse(as_epoch, FIXTURE) == as_strings


# --------------------------------------------------------------------------
# Rule 1.
# --------------------------------------------------------------------------

def test_second_run_doubles_the_rows_and_changes_none_of_the_first(conn, envelope):
    load(conn, envelope, "2026-09-12T06:00:00")
    first = conn.execute(
        "SELECT * FROM observations ORDER BY series_id, period_start"
    ).fetchall()

    load(conn, envelope, "2026-09-19T06:00:00")
    assert conn.execute("SELECT count(*) FROM observations").fetchone()[0] == len(first) * 2

    still_there = conn.execute(
        """
        SELECT * FROM observations WHERE received_at = TIMESTAMP '2026-09-12 06:00:00'
        ORDER BY series_id, period_start
        """
    ).fetchall()
    assert still_there == first


def test_replaying_the_same_fetch_adds_nothing(conn, envelope):
    assert load(conn, envelope, "2026-09-12T06:00:00") == 16  # 8 days x 2 series
    assert load(conn, envelope, "2026-09-12T06:00:00") == 0


def test_a_silent_backfill_appends_rather_than_overwrites(conn, envelope):
    """PortWatch rewrites recent days with no announcement. Both counts survive."""
    load(conn, envelope, "2026-09-12T06:00:00")
    backfilled = edit_features(
        envelope, lambda feats: feats[0]["attributes"].update(n_total=11)
    )
    load(conn, backfilled, "2026-09-19T06:00:00")

    counts = conn.execute(
        """
        SELECT value FROM observations
        WHERE series_id = 'hormuz_transits_total' AND period_start = DATE '2026-08-24'
        ORDER BY received_at
        """
    ).fetchall()
    assert counts == [(3.0,), (11.0,)]
    assert conn.execute(
        """
        SELECT value FROM observations_latest
        WHERE series_id = 'hormuz_transits_total' AND period_start = DATE '2026-08-24'
        """
    ).fetchone() == (11.0,)


# --------------------------------------------------------------------------
# What the rows say.
# --------------------------------------------------------------------------

def test_both_series_are_stored_against_the_canonical_entity(conn, envelope):
    """Rule 3: their portid is an alias, chokepoint:hormuz is the key."""
    load(conn, envelope, "2026-09-12T06:00:00")
    rows = conn.execute(
        "SELECT DISTINCT series_id, entity_id, unit FROM observations ORDER BY series_id"
    ).fetchall()
    assert rows == [
        ("hormuz_transits_tanker", "chokepoint:hormuz", "vessels"),
        ("hormuz_transits_total", "chokepoint:hormuz", "vessels"),
    ]
    assert conn.execute(
        "SELECT entity_id FROM entity_alias WHERE alias = 'chokepoint6'"
    ).fetchone() == ("chokepoint:hormuz",)


def test_a_day_with_no_tanker_count_is_still_a_row(conn, envelope):
    """"No count" and "no ships" are different facts. Keep the difference."""
    load(conn, envelope, "2026-09-12T06:00:00")
    missing, zero = conn.execute(
        """
        SELECT
          (SELECT value FROM observations WHERE series_id = 'hormuz_transits_tanker'
             AND period_start = DATE '2026-08-26'),
          (SELECT value FROM observations WHERE series_id = 'hormuz_transits_tanker'
             AND period_start = DATE '2026-08-28')
        """
    ).fetchone()
    assert missing is None, "a day PortWatch has no count for"
    assert zero == 0.0, "a day it counted no tankers"


def test_a_transit_count_covers_exactly_one_day(conn, envelope):
    load(conn, envelope, "2026-09-12T06:00:00")
    starts, ends = zip(*conn.execute(
        "SELECT period_start, period_end FROM observations"
    ).fetchall(), strict=True)
    assert starts == ends


def test_the_upstream_says_these_are_modelled_estimates(conn, envelope):
    """Rule 2, and the thing most likely to be forgotten about this feed."""
    load(conn, envelope, "2026-09-12T06:00:00")
    feed = conn.execute(
        "SELECT upstream, license_notes FROM feed_registry WHERE feed_id = ?",
        [portwatch.FEED_ID],
    ).fetchone()
    assert "AIS" in feed[0] and "modelled" in feed[0].lower()
    assert "portwatch.imf.org" in feed[1], "their terms require attribution"


# --------------------------------------------------------------------------
# Validation: structure, never plausibility.
# --------------------------------------------------------------------------

def test_a_good_reply_passes(envelope):
    portwatch.validate(envelope)


def test_a_collapse_to_zero_traffic_is_accepted(envelope):
    """August 2026 really did drop to single figures. Refusing it would discard
    the most informative weeks in the series."""
    zeroed = edit_features(envelope, lambda feats: [
        f["attributes"].update(n_total=0, n_tanker=0) for f in feats
    ])
    portwatch.validate(zeroed)  # must not raise


def test_a_row_for_another_chokepoint_is_refused(envelope):
    """If the server stops honouring the filter, another strait's traffic would
    be attached to Hormuz."""
    wrong = edit_features(envelope, lambda feats: feats[1]["attributes"].update(
        portid="chokepoint1", portname="Suez Canal"))
    with pytest.raises(ParseError, match="portid"):
        portwatch.validate(wrong)


def test_a_repeated_day_is_refused(envelope):
    doubled = edit_features(envelope, lambda feats: feats.append(copy.deepcopy(feats[0])))
    with pytest.raises(ParseError, match="twice"):
        portwatch.validate(doubled)


def test_a_date_in_the_future_is_refused(envelope):
    future = edit_features(
        envelope, lambda feats: feats[0]["attributes"].update(date="2099-01-01")
    )
    with pytest.raises(ParseError, match="future"):
        portwatch.validate(future)


def test_a_date_before_the_split_mask_starts_is_refused(envelope):
    """Those rows would be stored and then never appear in any view."""
    ancient = edit_features(
        envelope, lambda feats: feats[0]["attributes"].update(date="2014-12-31")
    )
    with pytest.raises(ParseError, match="split_mask"):
        portwatch.validate(ancient)


def test_a_server_error_is_refused_not_stored(envelope):
    envelope["responses"]["page_0"]["body"] = json.dumps(
        {"error": {"code": 400, "message": "Invalid query"}}
    )
    with pytest.raises(ParseError, match="error"):
        portwatch.validate(envelope)


# --------------------------------------------------------------------------
# run(), and the holdout.
# --------------------------------------------------------------------------

def test_a_whole_run_is_recorded(conn, offline_portwatch):
    result = portwatch.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))
    assert result.status == "ok"
    assert result.rows_inserted == 16
    assert conn.execute(
        "SELECT feed_id, status, rows_inserted FROM ingest_runs"
    ).fetchone() == ("portwatch_hormuz", "ok", 16)


def test_a_source_failure_is_recorded_and_returned_not_raised(
    conn, offline_portwatch, monkeypatch
):
    from core.errors import FeedError

    def refuse(feed_id, url, params=None, **kwargs):
        raise FeedError(feed_id, "no reply within 60s", url=url)

    monkeypatch.setattr("ingest.portwatch.get", refuse)
    result = portwatch.run(conn, received_at=datetime(2026, 9, 12, 6, 0, 0))

    assert result.status == "failed"
    assert conn.execute("SELECT count(*) FROM observations").fetchone()[0] == 0


def test_the_holdout_hides_whole_weeks_of_this_feed(conn, envelope):
    """The fixture spans two ISO weeks, and they are split differently."""
    load(conn, envelope, "2026-09-12T06:00:00")

    latest = conn.execute("SELECT count(*) FROM observations_latest").fetchone()[0]
    explore = conn.execute("SELECT count(*) FROM observations_explore").fetchone()[0]
    holdout = conn.execute("SELECT count(*) FROM observations_holdout").fetchone()[0]

    assert explore + holdout == latest
    assert explore and holdout, "the fixture must straddle the split to be worth testing"
    assert conn.execute(
        """
        SELECT count(*) FROM observations_explore e
        JOIN observations_holdout h USING (series_id, period_start)
        """
    ).fetchone()[0] == 0
