"""Tests for core/clock.py — everything stored is UTC, stored naive."""

from datetime import datetime, timedelta, timezone

from core import clock


def test_utc_now_has_no_timezone_attached():
    """Naive by convention: a TIMESTAMP in this database is UTC. See schema.sql."""
    assert clock.utc_now().tzinfo is None


def test_utc_now_really_is_utc():
    """Within a second of the reference clock, whatever zone the machine is in."""
    reference = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs(clock.utc_now() - reference) < timedelta(seconds=1)


def test_an_aware_time_is_converted_not_merely_stripped():
    """10:30 in British Summer Time is 09:30 UTC, and must be stored as 09:30."""
    bst = timezone(timedelta(hours=1))
    summer_morning = datetime(2026, 9, 11, 10, 30, tzinfo=bst)
    assert clock.to_utc_naive(summer_morning) == datetime(2026, 9, 11, 9, 30)


def test_a_naive_time_is_taken_at_its_word():
    already = datetime(2026, 9, 11, 9, 30)
    assert clock.to_utc_naive(already) == already


def test_the_clock_can_be_frozen(monkeypatch):
    """One place to freeze, so a test never depends on when it ran."""
    frozen = datetime(2026, 9, 11, 9, 0, 0)
    monkeypatch.setattr(clock, "utc_now", lambda: frozen)
    assert clock.utc_now() == frozen
