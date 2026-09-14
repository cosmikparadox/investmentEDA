"""Tests for `make ingest` — one feed failing must not stop the others (FR-07)."""

from datetime import datetime
from pathlib import Path

import duckdb
import pytest

from core import paths
from ingest import __main__ as ingest_all
from ingest.runs import finish_run, start_run

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def conn():
    connection = duckdb.connect(":memory:")
    connection.execute((paths.REPO_ROOT / "db" / "schema.sql").read_text())
    yield connection
    connection.close()


def fake_feed(feed_id: str, status: str):
    """A stand-in ingestor that records a run and reports the status we asked for."""

    class Feed:
        @staticmethod
        def run(connection, **kwargs):
            run_id = start_run(connection, feed_id, datetime(2026, 9, 14, 6, 0, 0))
            if status == "failed":
                return finish_run(connection, run_id, "failed", error="the source is down")
            return finish_run(connection, run_id, "ok", rows_fetched=10, rows_inserted=10)

    return Feed


def test_a_failing_feed_does_not_stop_the_others(conn, monkeypatch):
    monkeypatch.setattr(ingest_all, "FEEDS", (
        fake_feed("feed_a", "ok"),
        fake_feed("feed_b", "failed"),
        fake_feed("feed_c", "ok"),
    ))

    results = ingest_all.run_all(conn)

    assert [r.status for r in results] == ["ok", "failed", "ok"]
    assert [r.feed_id for r in results] == ["feed_a", "feed_b", "feed_c"]
    # The third feed ran after the second failed, and every attempt is recorded.
    assert conn.execute(
        "SELECT feed_id, status FROM ingest_runs ORDER BY run_id"
    ).fetchall() == [("feed_a", "ok"), ("feed_b", "failed"), ("feed_c", "ok")]


def test_the_summary_table_names_the_failure(conn, monkeypatch, capsys):
    monkeypatch.setattr(ingest_all, "FEEDS", (
        fake_feed("feed_a", "ok"), fake_feed("feed_b", "failed"),
    ))
    ingest_all.print_table(ingest_all.run_all(conn))

    printed = capsys.readouterr().out
    assert "feed_a" in printed and "feed_b" in printed
    assert "the source is down" in printed, "a failure must say why, not just 'failed'"


def test_the_real_feed_list_is_the_three_v0_feeds():
    """Written out by hand in ingest/__main__.py — no discovery, no registry."""
    assert [feed.FEED_ID for feed in ingest_all.FEEDS] == [
        "fred_brent_ovx", "eia_crude_stocks", "portwatch_hormuz",
    ]
