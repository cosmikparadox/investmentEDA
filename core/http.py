"""The one place this system makes an outbound request.

Every ingestor fetches through here, for four reasons:

  * timeouts are set explicitly, every time (NFR-05). A request with no timeout
    can hang until the process is killed, and a nightly ingest that hangs is
    indistinguishable from one that never ran.
  * failures come back as a FeedError carrying the feed, the URL with the key
    removed, the status and the first 500 characters of the reply (NFR-03).
  * API keys are stripped out of anything we record about the request.
  * it is the single function the tests replace, so no test ever touches the
    network (ARCHITECTURE.md §7).

`get()` returns the reply as text, exactly as it came off the wire, because
bronze stores the source's own bytes and not our reformatting of them.
`get_json()` is the same thing with the JSON already parsed, for callers that
do not need the raw text.
"""

import json
from dataclasses import dataclass
from urllib.parse import quote_plus, urlsplit, urlunsplit

import httpx

from core.errors import FeedError
from core.logging import get_logger, redact

# Time limits, in seconds. Connecting should be quick; a large history download
# is allowed to take a while. Named so the numbers are not a mystery.
CONNECT_TIMEOUT = 10.0
READ_TIMEOUT = 60.0

# Query parameters whose value is a secret and must never be written down.
SECRET_PARAMS = {"api_key", "apikey", "api-key", "key", "token", "access_token", "password"}

log = get_logger(__name__)


@dataclass(frozen=True)
class Response:
    """What came back: the status, the body as text, and a safe-to-print URL."""

    status_code: int
    text: str
    url: str  # already has any key replaced with ***


def safe_url(url: str, params: dict | None = None) -> str:
    """Rebuild a URL with secret parameters blanked out, for logs and errors."""
    parts = urlsplit(url)
    # Built by hand rather than with urlencode() so the masked value stays
    # readable as `api_key=***` instead of being escaped into `%2A%2A%2A`.
    shown = [
        f"{name}=***" if name.lower() in SECRET_PARAMS else f"{name}={quote_plus(str(value))}"
        for name, value in (params or {}).items()
    ]
    query = "&".join(shown) if shown else parts.query
    return redact(urlunsplit((parts.scheme, parts.netloc, parts.path, query, "")))


def get(
    feed_id: str,
    url: str,
    params: dict | None = None,
    *,
    connect_timeout: float = CONNECT_TIMEOUT,
    read_timeout: float = READ_TIMEOUT,
) -> Response:
    """Fetch a URL and return the reply as text. Raises FeedError if anything fails.

    "Fails" means: could not connect, took too long, or answered with a 4xx or
    5xx status. A feed that answers "500 Internal Server Error" with a page of
    HTML must not end up parsed and stored as if it were data.
    """
    shown = safe_url(url, params)
    timeout = httpx.Timeout(
        connect=connect_timeout, read=read_timeout, write=read_timeout, pool=connect_timeout
    )

    try:
        response = httpx.get(url, params=params, timeout=timeout)
    except httpx.TimeoutException as exc:
        raise FeedError(
            feed_id,
            f"no reply within {read_timeout:.0f}s ({type(exc).__name__})",
            url=shown,
        ) from exc
    except httpx.HTTPError as exc:
        # Covers DNS failures, refused connections, TLS problems and the like.
        raise FeedError(feed_id, f"request failed: {exc}", url=shown) from exc

    if response.status_code >= 400:
        raise FeedError(
            feed_id,
            f"HTTP {response.status_code}",
            url=shown,
            status=response.status_code,
            body=response.text,
        )

    log.debug("fetched %s (%d chars)", shown, len(response.text), extra={"feed": feed_id})
    return Response(status_code=response.status_code, text=response.text, url=shown)


def get_json(
    feed_id: str,
    url: str,
    params: dict | None = None,
    *,
    connect_timeout: float = CONNECT_TIMEOUT,
    read_timeout: float = READ_TIMEOUT,
) -> dict:
    """Fetch a URL and return the reply already turned into Python data.

    Use `get()` instead when the exact text is needed — an ingestor writing a
    bronze file needs the source's own bytes, not our re-serialised copy of them.
    """
    response = get(
        feed_id,
        url,
        params,
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
    )
    try:
        return json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise FeedError(
            feed_id,
            f"reply is not valid JSON ({exc})",
            url=response.url,
            status=response.status_code,
            body=response.text,
        ) from exc
