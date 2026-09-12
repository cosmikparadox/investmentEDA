"""Tests for the shared plumbing in core/.

These test the things that are easy to get wrong and expensive to get wrong:
that an API key cannot reach a log line or an error message, that a path means
the same thing wherever it is resolved from, that a missing key produces a
message a human can act on, and that a failed request becomes a typed error
carrying enough context to debug it.

Nothing here touches the network. core.http.get is the one function the tests
replace (ARCHITECTURE.md §7).
"""

import json
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from core import config, http, logging as clog, paths
from core.errors import BODY_CHARS, ConfigError, FeedError, ParseError, StorageError

FAKE_KEY = "abcd1234efgh5678ijkl"


# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------

def test_repo_root_is_the_repo():
    assert (paths.REPO_ROOT / "CLAUDE.md").exists()
    assert (paths.REPO_ROOT / "db" / "schema.sql").exists()


def test_bronze_path_has_no_colons():
    """Windows will not open a file with a colon in its name (PRD DR-05)."""
    path = paths.bronze_path("fred_brent_ovx", datetime(2026, 9, 11, 14, 30, 5))
    assert path.name == "2026-09-11T14-30-05.json"
    assert ":" not in path.name
    assert path.parent == paths.BRONZE_DIR / "fred_brent_ovx"


def test_from_repo_root_keeps_absolute_paths_and_anchors_relative_ones():
    assert paths.from_repo_root("data/x.duckdb") == paths.REPO_ROOT / "data/x.duckdb"
    assert paths.from_repo_root("/tmp/x.duckdb") == Path("/tmp/x.duckdb")


def test_relative_to_repo_shortens_inside_and_leaves_outside_alone():
    inside = paths.REPO_ROOT / "data" / "bronze" / "f" / "x.json"
    assert paths.relative_to_repo(inside) == "data/bronze/f/x.json"
    assert paths.relative_to_repo("/etc/hosts") == "/etc/hosts"


# --------------------------------------------------------------------------
# redaction — the one that matters most
# --------------------------------------------------------------------------

def test_a_registered_secret_is_never_printed():
    clog.register_secret(FAKE_KEY)
    assert FAKE_KEY not in clog.redact(f"...api_key={FAKE_KEY}&file_type=json")
    assert "***" in clog.redact(f"api_key={FAKE_KEY}")


def test_short_values_are_not_treated_as_secrets():
    """A two-character 'secret' would blank out ordinary text everywhere."""
    clog.register_secret("ab")
    assert clog.redact("a table of abbreviations") == "a table of abbreviations"


def test_log_lines_have_the_expected_shape_and_no_key(caplog):
    log = clog.get_logger("tests.demo", "fred_brent_ovx")
    clog.register_secret(FAKE_KEY)
    with caplog.at_level("INFO"):
        log.info("fetched with %s", FAKE_KEY)
    record = caplog.records[-1]
    assert record.feed == "fred_brent_ovx"
    assert FAKE_KEY not in clog.redact(record.getMessage())


def test_secret_params_are_masked_in_a_url():
    shown = http.safe_url(
        "https://api.stlouisfed.org/fred/series/observations",
        {"series_id": "OVXCLS", "api_key": FAKE_KEY, "file_type": "json"},
    )
    assert "api_key=***" in shown
    assert FAKE_KEY not in shown
    assert "series_id=OVXCLS" in shown  # ordinary parameters survive


def test_settings_repr_does_not_show_the_keys():
    """print(settings) must not put a key on screen, or into a chat window."""
    shown = repr(config.Settings(FAKE_KEY, FAKE_KEY, "INFO", Path("data/x.duckdb")))
    assert FAKE_KEY not in shown
    assert "set" in shown


# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------

def test_missing_key_says_which_key_and_where_to_get_one(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.setattr(config, "settings", config.Settings(None, None, "INFO", Path("x")))
    with pytest.raises(ConfigError) as caught:
        config.api_key("FRED_API_KEY")
    message = str(caught.value)
    assert "FRED_API_KEY" in message
    assert "fredaccount.stlouisfed.org" in message


def test_a_present_key_is_returned(monkeypatch):
    monkeypatch.setattr(
        config, "settings", config.Settings(None, FAKE_KEY, "INFO", Path("x"))
    )
    assert config.api_key("FRED_API_KEY") == FAKE_KEY


def test_importing_config_without_keys_does_not_explode(monkeypatch):
    """db/init.py, the tests and the dashboard all run on a machine with no keys."""
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    settings = config.Settings(None, None, "INFO", Path("data/controlroom.duckdb"))
    assert settings.fred_api_key is None


# --------------------------------------------------------------------------
# http — every call is a fake; nothing here goes near a network
# --------------------------------------------------------------------------

def _fake_get(status: int, text: str):
    def _get(url, params=None, timeout=None):
        request = httpx.Request("GET", url, params=params)
        return httpx.Response(status_code=status, text=text, request=request)
    return _get


def test_get_returns_the_body_verbatim(monkeypatch):
    """Bronze stores the source's own bytes, so nothing may reformat them."""
    body = '{"observations": [{"date": "2026-09-01", "value": "68.4"}]}'
    monkeypatch.setattr(httpx, "get", _fake_get(200, body))
    response = http.get("fred_brent_ovx", "https://example.test/x", {"api_key": FAKE_KEY})
    assert response.text == body
    assert response.status_code == 200
    assert FAKE_KEY not in response.url


def test_an_error_status_becomes_a_feed_error_with_context(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get(429, "slow down"))
    with pytest.raises(FeedError) as caught:
        http.get("fred_brent_ovx", "https://example.test/x", {"api_key": FAKE_KEY})
    error = caught.value
    assert error.status == 429
    assert error.feed_id == "fred_brent_ovx"
    assert "slow down" in error.body
    assert FAKE_KEY not in str(error)


def test_a_long_error_body_is_trimmed(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get(500, "x" * 5000))
    with pytest.raises(FeedError) as caught:
        http.get("eia_crude_stocks", "https://example.test/x")
    assert len(caught.value.body) == BODY_CHARS


def test_a_timeout_becomes_a_feed_error(monkeypatch):
    def _timeout(url, params=None, timeout=None):
        raise httpx.ReadTimeout("too slow")
    monkeypatch.setattr(httpx, "get", _timeout)
    with pytest.raises(FeedError) as caught:
        http.get("fred_brent_ovx", "https://example.test/x")
    assert "no reply within" in str(caught.value)


def test_get_json_parses_and_reports_bad_json(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get(200, '{"a": 1}'))
    assert http.get_json("f", "https://example.test/x") == {"a": 1}

    monkeypatch.setattr(httpx, "get", _fake_get(200, "<html>maintenance</html>"))
    with pytest.raises(FeedError) as caught:
        http.get_json("f", "https://example.test/x")
    assert "not valid JSON" in str(caught.value)


def test_timeouts_are_always_set(monkeypatch):
    """A request with no timeout can hang until someone notices. NFR-05."""
    seen = {}

    def _capture(url, params=None, timeout=None):
        seen["timeout"] = timeout
        return httpx.Response(200, text="{}", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", _capture)
    http.get("f", "https://example.test/x")
    assert seen["timeout"].connect == http.CONNECT_TIMEOUT
    assert seen["timeout"].read == http.READ_TIMEOUT


# --------------------------------------------------------------------------
# errors
# --------------------------------------------------------------------------

def test_each_error_names_the_feed_and_keeps_its_context():
    feed = FeedError("f", "HTTP 500", url="https://x.test?api_key=***", status=500, body="oops")
    assert "f: HTTP 500" in str(feed)
    assert "status=500" in str(feed)

    parse = ParseError("f", "no 'observations' key", bronze_path="data/bronze/f/x.json")
    assert "data/bronze/f/x.json" in str(parse)

    storage = StorageError("f", "insert failed", target="observations", cause="disk full")
    assert "observations" in str(storage) and "disk full" in str(storage)


def test_errors_redact_secrets_that_reach_them():
    clog.register_secret(FAKE_KEY)
    error = FeedError("f", "boom", url=f"https://x.test?api_key={FAKE_KEY}")
    assert FAKE_KEY not in str(error)


def test_a_secret_in_a_log_argument_is_redacted_too(caplog):
    """The leak this filter missed once: httpx logs the URL as an argument.

    `log.info("GET %s", url)` keeps the URL in record.args, so redacting only
    record.msg leaves the key in the output. It has to be formatted first.
    """
    clog.register_secret(FAKE_KEY)
    log = clog.get_logger("tests.demo")
    with caplog.at_level("INFO"):
        log.info("GET %s", f"https://x.test/series?api_key={FAKE_KEY}")
    line = caplog.records[-1].getMessage()
    assert FAKE_KEY not in line
    assert "***" in line
