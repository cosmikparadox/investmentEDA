"""The test that keeps rule 4 true: the app cannot reach the holdout.

PRD FR-44 says the app never imports or queries the all-vintages view or the
holdout view. This checks it the bluntest way there is — by reading every file
under app/ and looking for their names. A blunt test is the right kind here:
the failure it prevents is silent, and by the time anyone noticed, months of
looking at data that was supposed to be untouched would already have happened.

It also means those names must not appear in app/ even inside a comment. That
feels petty until you remember what the alternative is: a comment saying "we
must never query observations_holdout" sitting one uncommented character away
from doing exactly that.
"""

from pathlib import Path

import duckdb
import pytest

from app import queries
from core import paths

APP = paths.REPO_ROOT / "app"

# Spelled in pieces so that this file — which is not under app/ — can name them
# without the check below finding its own text if anyone ever moves it.
FORBIDDEN = ("observations_" + "latest", "observations_" + "holdout")


def app_files() -> list[Path]:
    return sorted(APP.rglob("*.py"))


def test_there_is_an_app_to_check():
    assert app_files(), "no files under app/ — this test would pass vacuously"


@pytest.mark.parametrize("name", FORBIDDEN)
def test_the_app_never_names_the_views_it_may_not_read(name):
    offenders = [
        f"{path.relative_to(paths.REPO_ROOT)}:{number}"
        for path in app_files()
        for number, line in enumerate(path.read_text().splitlines(), start=1)
        if name in line
    ]
    assert not offenders, (
        f"{name} appears in app/ at {offenders}. The app reads the explore view "
        f"and nothing else — see PRD FR-44 and rule 4 in CLAUDE.md."
    )


def test_the_app_reads_the_explore_view():
    """The other half: it must actually be reading the right one."""
    sources = "\n".join(path.read_text() for path in app_files())
    assert "observations_explore" in sources


def test_there_is_no_show_everything_control(monkeypatch):
    """UI-08: no toggle, anywhere, ever."""
    sources = "\n".join(path.read_text().lower() for path in app_files())
    for phrase in ("show all", "show everything", "include holdout", "unfiltered"):
        assert phrase not in sources.replace("everything we may look at", ""), phrase


# --------------------------------------------------------------------------
# The queries themselves, against a small synthetic database.
# --------------------------------------------------------------------------

@pytest.fixture
def conn(tmp_path, monkeypatch):
    from core import config

    db_path = tmp_path / "test.duckdb"
    connection = duckdb.connect(str(db_path))
    connection.execute((paths.REPO_ROOT / "db" / "schema.sql").read_text())
    connection.execute((paths.REPO_ROOT / "db" / "seed_entities.sql").read_text())
    connection.execute(
        "INSERT INTO split_mask VALUES ('2026-W36', 'explore'), ('2026-W37', 'holdout')"
    )
    connection.execute(
        """
        INSERT INTO feed_registry VALUES
        ('test_feed', 'A provider', 'A survey', 'daily', 'https://x.test',
         NULL, DATE '2026-09-14')
        """
    )
    for period, value in (("2026-08-31", 68.0), ("2026-09-07", 69.0)):
        connection.execute(
            """
            INSERT INTO observations (feed_id, series_id, entity_id, period_start,
                period_end, value, unit, received_at, source_asof, bronze_path, parse_version)
            VALUES ('test_feed', 'test_series', 'benchmark:brent', ?, ?, ?, 'usd_per_bbl',
                    TIMESTAMP '2026-09-14 06:00:00', NULL, 'data/bronze/x.json', 1)
            """,
            [period, period, value],
        )
    connection.close()

    # Settings is frozen, so point the app at the test database by swapping the
    # whole object — and swap it where the app looked it up, since `from ...
    # import settings` binds the object, not the module attribute.
    test_settings = config.Settings(None, None, "INFO", db_path)
    monkeypatch.setattr(config, "settings", test_settings)
    monkeypatch.setattr(queries, "settings", test_settings)
    return db_path


def test_the_catalogue_shows_only_what_may_be_looked_at(conn):
    connection = queries.connect()
    try:
        catalogue = queries.series_catalogue(connection)
    finally:
        connection.close()

    assert list(catalogue["series_id"]) == ["test_series"]
    # 2026-W37 is holdout, so the 7 September row must not be counted or shown.
    assert int(catalogue.iloc[0]["rows_shown"]) == 1
    assert str(catalogue.iloc[0]["last_period"]).startswith("2026-08-31")


def test_a_note_is_written_with_what_was_on_screen(conn):
    from datetime import date

    queries.write_note("brent drifted up all week", ["test_series"],
                       date(2026, 8, 1), date(2026, 9, 14))

    connection = duckdb.connect(str(conn))
    try:
        row = connection.execute(
            "SELECT note, series_ids, window_start, window_end, status FROM observation_log"
        ).fetchone()
    finally:
        connection.close()

    assert row[0] == "brent drifted up all week"
    assert list(row[1]) == ["test_series"]
    assert (row[2], row[3]) == (date(2026, 8, 1), date(2026, 9, 14))
    assert row[4] == "noted", "a new note starts as noted, untested"


def test_the_app_opens_the_database_read_only(conn):
    """The dashboard has no business writing to observations, so it cannot."""
    connection = queries.connect()
    try:
        with pytest.raises(duckdb.Error):
            connection.execute("DELETE FROM observations")
    finally:
        connection.close()


def test_a_missing_week_becomes_a_break_in_the_line():
    """UI-01: the gap must be drawn as a gap, not interpolated across."""
    import pandas as pd

    from app.dashboard import break_the_line_at_missing_weeks

    frame = pd.DataFrame({
        "period_start": pd.to_datetime(["2026-08-31", "2026-09-14"]),  # W37 missing
        "value": [68.0, 70.0],
    })
    broken = break_the_line_at_missing_weeks(frame)

    assert len(broken) == 3, "an empty point must be inserted in the missing week"
    assert broken["value"].isna().sum() == 1
    gap_at = broken.loc[broken["value"].isna(), "period_start"].iloc[0]
    assert gap_at.strftime("%G-W%V") == "2026-W37"


def test_a_continuous_series_is_left_alone():
    import pandas as pd

    from app.dashboard import break_the_line_at_missing_weeks

    frame = pd.DataFrame({
        "period_start": pd.to_datetime(["2026-08-31", "2026-09-07", "2026-09-14"]),
        "value": [68.0, 69.0, 70.0],
    })
    assert len(break_the_line_at_missing_weeks(frame)) == 3
