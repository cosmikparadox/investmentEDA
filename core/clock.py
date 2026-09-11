"""The one place this system asks what time it is.

Everything stored in the database is UTC. Not local time, not the owner's time
zone, not the source's — UTC, always, in every TIMESTAMP column.

Why it matters here more than in most projects: `received_at` is part of the
primary key of `observations`. It is the answer to "what did we know, and when".
If half the rows are written in British Summer Time and half in UTC, then "what
did we know on 5 September" is wrong by an hour at the boundary, and nothing in
the data says which rows are which. A database that cannot answer its own
central question is worse than one that is merely inconvenient.

Stored naive, meaning the value carries no time zone marker — the convention is
that a TIMESTAMP in this database is UTC, and it is written down at the top of
db/schema.sql. DuckDB does have a time-zone-aware type, but mixing the two makes
every comparison a question about which is which. One convention, applied
everywhere, is easier to keep true than a type system nobody remembers.

Everything goes through `utc_now()` so that tests can freeze time in one place:

    monkeypatch.setattr(clock, "utc_now", lambda: datetime(2026, 9, 11, 9, 0, 0))

For that to work, import the module and call `clock.utc_now()` — not
`from core.clock import utc_now`, which takes a copy of the function that
monkeypatching the module cannot reach.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """The current time in UTC, ready to store: no time zone attached.

    The tzinfo is stripped here, at the boundary, rather than by each caller —
    the value is UTC whether or not it is labelled, and labelling it would mean
    DuckDB storing it in a different column type from every other timestamp.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc_naive(moment: datetime) -> datetime:
    """Convert any datetime to the form the database stores.

    An aware datetime (one that knows its offset, e.g. 10:30 BST) is converted
    to UTC and then stripped, so 10:30 BST becomes 09:30. A naive one is assumed
    to be UTC already and returned unchanged — that is the convention, and
    guessing a zone for it would be worse than trusting it.
    """
    if moment.tzinfo is None:
        return moment
    return moment.astimezone(timezone.utc).replace(tzinfo=None)
