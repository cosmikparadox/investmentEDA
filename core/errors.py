"""The three kinds of thing that go wrong, each carrying enough context to act on.

Why typed errors rather than plain `Exception`: when a feed breaks at 6am the
message in `ingest_runs` is all you have. "KeyError: 'observations'" tells you
nothing. "fred_brent_ovx: no 'observations' key in the reply (bronze=data/...)"
tells you which feed, which file to look at, and what was wrong.

Rule, from ARCHITECTURE.md §4: never swallow an exception. Catch a specific one,
convert it to one of these with context attached, and let it travel.
"""

# How much of a server's reply we keep in an error message. Enough to see an
# error page or a JSON error body; not so much that a log line becomes a wall.
BODY_CHARS = 500


class ControlroomError(Exception):
    """Base class for every error this system raises on purpose.

    Catching `ControlroomError` means "something we anticipated went wrong".
    A programmer error — a typo, a bad import — is not one of these and should
    crash loudly instead.
    """


class FeedError(ControlroomError):
    """A source could not be reached, refused us, or answered with nonsense.

    Carries the feed, the URL with any key removed, the HTTP status if there was
    one, and the first 500 characters of the reply.
    """

    def __init__(
        self,
        feed_id: str,
        message: str,
        *,
        url: str | None = None,
        status: int | None = None,
        body: str | None = None,
    ) -> None:
        self.feed_id = feed_id
        self.url = url
        self.status = status
        self.body = (body or "")[:BODY_CHARS] or None
        super().__init__(
            _describe(
                feed_id,
                message,
                url=url,
                status=status,
                body=self.body,
            )
        )


class ParseError(ControlroomError):
    """A payload was saved successfully but does not have the shape we expect.

    The bronze file always survives a ParseError — that is the point of writing
    it before parsing — so `bronze_path` is the first thing to look at.
    """

    def __init__(
        self,
        feed_id: str,
        message: str,
        *,
        bronze_path: str | None = None,
        field: str | None = None,
        sample: str | None = None,
    ) -> None:
        self.feed_id = feed_id
        self.bronze_path = bronze_path
        self.field = field
        self.sample = (sample or "")[:BODY_CHARS] or None
        super().__init__(
            _describe(
                feed_id,
                message,
                bronze=bronze_path,
                field=field,
                sample=self.sample,
            )
        )


class StorageError(ControlroomError):
    """Writing failed — a bronze file could not be written, or a row could not
    be inserted. The underlying message is kept as `cause`."""

    def __init__(
        self,
        feed_id: str,
        message: str,
        *,
        target: str | None = None,
        cause: str | None = None,
    ) -> None:
        self.feed_id = feed_id
        self.target = target
        self.cause = cause
        super().__init__(_describe(feed_id, message, target=target, cause=cause))


class ConfigError(ControlroomError):
    """Something the system needs is not in the environment or the .env file.

    Always names the missing setting and how to get one, because the person
    reading it is usually the person who has to go and fetch a key.
    """


def _describe(feed_id: str, message: str, **context: object) -> str:
    """Build the one-line error text: what failed, for which feed, what to check.

    Redaction happens here as a last line of defence: by the time a URL or a
    reply body reaches an error message it should already have had keys removed,
    but doing it again costs nothing and a leaked key is not recoverable.
    """
    from core.logging import redact  # imported here to keep the import graph flat

    parts = [f"{feed_id}: {message}"] if feed_id else [message]
    for name, value in context.items():
        if value is not None and value != "":
            parts.append(f"{name}={value!r}")
    return redact(" ".join(parts))
