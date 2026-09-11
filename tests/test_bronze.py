"""Tests for ingest/bronze.py — the raw layer, and the promises it makes.

Three things are checked: that a file holds exactly the bytes a source sent,
that an existing file is never overwritten (rule 1, at its most literal), and
that a crash mid-write cannot leave a half-written file that later looks like
evidence.
"""

from datetime import datetime
from pathlib import Path

import pytest

from core import paths
from core.errors import StorageError
from ingest import bronze

FEED = "test_feed"
RECEIVED_AT = datetime(2026, 9, 11, 9, 0, 0)
PAYLOAD = b'{"observations": [{"date": "2026-09-01", "value": "68.4"}]}'


@pytest.fixture
def bronze_root(tmp_path, monkeypatch):
    """Point the bronze folder at a throwaway directory for the duration.

    tmp_path is pytest's per-test scratch directory, so nothing here touches the
    real data/bronze/ and nothing survives the test.
    """
    monkeypatch.setattr(paths, "BRONZE_DIR", tmp_path / "bronze")
    return tmp_path / "bronze"


def test_the_file_holds_exactly_what_was_sent(bronze_root):
    path = bronze.write_bronze(FEED, RECEIVED_AT, PAYLOAD)
    assert path.read_bytes() == PAYLOAD
    assert bronze.read_bronze(path) == PAYLOAD


def test_the_path_is_the_documented_one(bronze_root):
    """data/bronze/<feed_id>/<received_at>.json, colons to hyphens (DR-05)."""
    path = bronze.write_bronze(FEED, RECEIVED_AT, PAYLOAD)
    assert path == bronze_root / FEED / "2026-09-11T09-00-00.json"
    assert ":" not in path.name


def test_the_folder_is_created_if_it_is_not_there(bronze_root):
    assert not bronze_root.exists()
    bronze.write_bronze(FEED, RECEIVED_AT, PAYLOAD)
    assert (bronze_root / FEED).is_dir()


def test_an_existing_file_is_never_overwritten(bronze_root):
    """Rule 1 at its most literal: the evidence is not written over."""
    bronze.write_bronze(FEED, RECEIVED_AT, PAYLOAD)
    with pytest.raises(StorageError) as caught:
        bronze.write_bronze(FEED, RECEIVED_AT, b"something else entirely")
    assert "will not be overwritten" in str(caught.value)
    # and the original is untouched
    assert bronze.read_bronze(paths.bronze_path(FEED, RECEIVED_AT)) == PAYLOAD


def test_no_temporary_file_is_left_behind(bronze_root):
    """A .part file lying around would eventually be mistaken for data."""
    bronze.write_bronze(FEED, RECEIVED_AT, PAYLOAD)
    leftovers = [p.name for p in (bronze_root / FEED).iterdir() if p.suffix == ".part"]
    assert leftovers == []


def test_a_failed_write_leaves_nothing_at_the_real_path(bronze_root, monkeypatch):
    """Half a file is worse than no file: it looks like evidence and is not."""
    def _explode(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("ingest.bronze.os.replace", _explode)
    with pytest.raises(StorageError) as caught:
        bronze.write_bronze(FEED, RECEIVED_AT, PAYLOAD)
    assert "disk full" in str(caught.value)
    assert not paths.bronze_path(FEED, RECEIVED_AT).exists()
    assert [p for p in (bronze_root / FEED).iterdir()] == []  # temp cleaned up too


def test_text_is_refused_with_an_explanation(bronze_root):
    """Bronze keeps bytes. A str has already been decoded by somebody."""
    with pytest.raises(TypeError) as caught:
        bronze.write_bronze(FEED, RECEIVED_AT, '{"already": "a string"}')
    assert "encode it first" in str(caught.value).lower()


def test_reading_a_file_that_is_not_there_says_so():
    with pytest.raises(StorageError) as caught:
        bronze.read_bronze(Path("/nowhere/at/all.json"))
    assert "could not read" in str(caught.value)


def test_two_different_moments_are_two_different_files(bronze_root):
    first = bronze.write_bronze(FEED, RECEIVED_AT, PAYLOAD)
    second = bronze.write_bronze(FEED, datetime(2026, 9, 12, 9, 0, 0), b"tomorrow")
    assert first != second
    assert first.read_bytes() == PAYLOAD and second.read_bytes() == b"tomorrow"
