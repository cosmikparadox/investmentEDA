"""Fetch US crude oil stocks from the EIA into `observations`.

The EIA is the US Energy Information Administration. Every Wednesday it
publishes the Weekly Petroleum Status Report, and the number we take from it is:

    WCESTUS1   US ending stocks of crude oil, excluding the Strategic Petroleum
               Reserve, in thousands of barrels

"Ending stocks" means how much crude was sitting in commercial tanks at the end
of that week — a level, not a flow. It is one of the most watched numbers in the
oil market, because a build means more supply than demand that week and a draw
means the opposite.

Why this feed matters more than its one series suggests: **the EIA revises it.**
A number published for last week can change in a later release, and the API only
ever serves the current value — there is no way to ask what it said last
Wednesday. Every pull is therefore a snapshot with our own `received_at` on it,
and the accumulated snapshots are the only record anywhere of what was known
when. This feed is the reason the whole system is built the way it is.

Run it the same way as every other ingestor:

    uv run python -m ingest.eia
    uv run python -m ingest.eia --reparse FILE --reason "..."
"""

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb

from core import clock, paths
from core.config import api_key, settings
from core.errors import ControlroomError, ParseError, StorageError
from core.http import get
from core.logging import get_logger
from ingest.bronze import read_bronze, write_bronze
from ingest.runs import RunResult, finish_run, start_run

FEED_ID = "eia_crude_stocks"
ENDPOINT = "https://api.eia.gov/v2/petroleum/sum/sndw/data/"

# The country this stock level is about. ISO 3166-1 alpha-3, per rule 3.
ENTITY_ID = "country:USA"

# The EIA's name for the series -> (our name for it, what it is measured in).
# MBBL is the EIA's own unit string: M is the Roman thousand, so it means
# thousands of barrels. We store it under our canonical name, `kbbl`, because
# "M for thousand" is a trap for anyone reading it later.
EIA_SERIES = "WCESTUS1"
SERIES_ID = "us_crude_stocks_ex_spr"
UNIT = "kbbl"
EXPECTED_UNITS = "MBBL"

# split_mask only covers ISO weeks 2015-2030, and observations_explore joins
# against it, so anything older would be stored and never displayed.
DEFAULT_START = "2015-01-01"

# The EIA caps a single reply at 5000 rows. Weekly data since 2015 is about 600,
# so one page is normally enough — but the code pages anyway, because "normally
# enough" is how a feed silently truncates two years from now.
PAGE_SIZE = 5000

ENVELOPE_VERSION = 1

log = get_logger(__name__, FEED_ID)


def fetch(observation_start: str, received_at: datetime) -> bytes:
    """Ask the EIA for the series and wrap every page, verbatim, in an envelope.

    Returns the bytes to write to bronze. Each page is stored as the exact text
    the EIA sent, in the order it arrived. The API key is deliberately not
    recorded: a secret in a data file is a secret you forget you wrote down.
    """
    key = api_key("EIA_API_KEY")

    pages: dict[str, dict] = {}
    offset = 0
    while True:
        reply = get(
            FEED_ID,
            ENDPOINT,
            params={
                "api_key": key,
                "frequency": "weekly",
                "data[0]": "value",
                "facets[series][]": EIA_SERIES,
                "sort[0][column]": "period",
                "sort[0][direction]": "asc",
                "start": observation_start,
                "offset": offset,
                "length": PAGE_SIZE,
            },
        )
        pages[f"page_{len(pages)}"] = {
            "status": reply.status_code,
            "offset": offset,
            "body": reply.text,  # verbatim, exactly as it came off the wire
        }

        body = json.loads(reply.text)
        total = int(body.get("response", {}).get("total", 0))
        returned = len(body.get("response", {}).get("data", []))
        offset += returned
        log.debug("page %d: %d of %d rows", len(pages) - 1, offset, total)

        # Stop when we have them all, or when a page comes back empty — without
        # that second condition a server that always returns nothing would spin
        # here for ever.
        if offset >= total or returned == 0:
            break

    return json.dumps(
        {
            "envelope_version": ENVELOPE_VERSION,
            "feed_id": FEED_ID,
            "received_at": received_at.isoformat(),
            "endpoint": ENDPOINT,
            "request": {
                "series": EIA_SERIES,
                "frequency": "weekly",
                "start": observation_start,
                "length": PAGE_SIZE,
            },
            "responses": pages,
        },
        indent=2,
    ).encode()


def read_envelope(path: str | Path) -> dict:
    """Read a bronze file back and check it is a shape this code understands."""
    payload = read_bronze(path)
    try:
        envelope = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ParseError(FEED_ID, f"not valid JSON ({exc})", bronze_path=str(path)) from exc

    version = envelope.get("envelope_version")
    if version != ENVELOPE_VERSION:
        raise ParseError(
            FEED_ID,
            f"this is a version {version!r} bronze file; this code reads version "
            f"{ENVELOPE_VERSION}",
            bronze_path=str(path),
            field="envelope_version",
        )
    return envelope


def rows_of(envelope: dict) -> list[dict]:
    """Every data row from every page, in the order they arrived."""
    collected = []
    for name in sorted(envelope["responses"], key=lambda n: int(n.split("_")[1])):
        body = json.loads(envelope["responses"][name]["body"])
        collected.extend(body.get("response", {}).get("data", []))
    return collected


def validate(envelope: dict, bronze_path: str | Path | None = None) -> None:
    """Check the reply is the shape we expect, before any of it is stored.

    Structure, not plausibility. A stock level that jumps unexpectedly is news,
    not an error — the one thing this refuses on content is a change of units,
    because that would silently make every stored number mean something else.
    """
    where = str(bronze_path) if bronze_path else None

    def refuse(message: str, field: str | None = None, sample: str | None = None):
        raise ParseError(FEED_ID, message, bronze_path=where, field=field, sample=sample)

    first_body = json.loads(envelope["responses"]["page_0"]["body"])
    if "response" not in first_body:
        error = first_body.get("error", "no 'response' key")
        refuse(f"the reply is not data: {error}", field="response")

    rows = rows_of(envelope)
    if not rows:
        refuse("zero rows returned", field="data")

    total = int(first_body["response"].get("total", 0))
    if len(rows) < total:
        refuse(
            f"only {len(rows)} of {total} rows were fetched — paging stopped early "
            f"and storing this would look like the series simply ends",
            field="total",
        )

    requested_start = date.fromisoformat(envelope["request"]["start"])
    latest_sane = date.today() + timedelta(days=1)
    seen = set()

    for row in rows:
        try:
            period = date.fromisoformat(row["period"])
        except (KeyError, ValueError) as exc:
            refuse(f"unusable period ({exc})", field="period", sample=str(row)[:200])
        if period in seen:
            refuse(f"{period} appears twice", field="period", sample=str(period))
        seen.add(period)
        if not requested_start <= period <= latest_sane:
            refuse(
                f"{period} is outside the window we asked for "
                f"({requested_start} to {latest_sane})",
                field="period",
                sample=str(period),
            )

        units = row.get("units")
        if units != EXPECTED_UNITS:
            refuse(
                f"{period} is in {units!r}, not {EXPECTED_UNITS!r} — the EIA has "
                f"changed units and every stored number would mean something else",
                field="units",
                sample=repr(units),
            )

        raw = row.get("value")
        if raw is not None:
            try:
                float(raw)
            except (TypeError, ValueError):
                refuse(f"{period} value {raw!r}", field="value", sample=repr(raw))


def parse(envelope: dict, bronze_path: str | Path, parse_version: int = 1) -> list[tuple]:
    """Turn a bronze envelope into rows shaped like the `observations` table.

    A pure function: no network, no database, no clock. `received_at` comes from
    the envelope so that re-reading an old file and fetching fresh data go down
    exactly the same path.

    `period_start` and `period_end` are both the reported date, because this is
    a *stock*: the level of crude in tanks at the end of that Friday, not a flow
    spread across the week. Giving it a seven-day span would claim the number
    describes the whole week, which it does not.
    """
    received_at = datetime.fromisoformat(envelope["received_at"])
    recorded_path = paths.relative_to_repo(bronze_path)

    rows = []
    for row in rows_of(envelope):
        period = date.fromisoformat(row["period"])
        raw = row.get("value")
        # A missing value stays a row with no number. A week the EIA did not
        # publish is information, and dropping it would hide that.
        value = None if raw is None else float(raw)

        rows.append((
            FEED_ID,
            SERIES_ID,
            ENTITY_ID,
            period,
            period,
            value,
            UNIT,
            received_at,
            # The EIA does not say when it published this number, so we cannot
            # claim to know. Their release schedule is Wednesday 10:30 ET, but a
            # schedule is not a timestamp. NULL is the honest answer.
            None,
            recorded_path,
            parse_version,
        ))
    return rows


def register_feed(conn: duckdb.DuckDBPyConnection) -> None:
    """Record what this feed is and where it really comes from (rule 2)."""
    conn.execute(
        """
        INSERT OR IGNORE INTO feed_registry
            (feed_id, provider, upstream, cadence, endpoint, license_notes, added_on)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            FEED_ID,
            "US EIA, API v2",
            "EIA weekly survey of commercial crude oil stocks (Weekly Petroleum Status Report)",
            "weekly",
            ENDPOINT,
            "US government work, public domain. Cite EIA.",
            date.today(),
        ],
    )


def next_parse_version(conn: duckdb.DuckDBPyConnection, bronze_path: str | Path) -> int:
    """1 if this file has never been loaded, else one past its highest version."""
    highest = conn.execute(
        """
        SELECT coalesce(max(parse_version), 0) FROM observations
        WHERE feed_id = ? AND bronze_path = ?
        """,
        [FEED_ID, paths.relative_to_repo(bronze_path)],
    ).fetchone()[0]
    return int(highest) + 1


def store(conn: duckdb.DuckDBPyConnection, rows: list[tuple]) -> int:
    """Add rows in one transaction, skip any already present, report how many were new."""
    register_feed(conn)
    before = conn.execute("SELECT count(*) FROM observations").fetchone()[0]

    conn.execute("BEGIN TRANSACTION")
    try:
        conn.executemany(
            """
            INSERT OR IGNORE INTO observations
                (feed_id, series_id, entity_id, period_start, period_end,
                 value, unit, received_at, source_asof, bronze_path, parse_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.execute("COMMIT")
    except duckdb.Error as exc:
        conn.execute("ROLLBACK")
        raise StorageError(
            FEED_ID, "could not insert the parsed rows", target="observations",
            cause=str(exc),
        ) from exc

    after = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    return after - before


def record_correction(
    conn: duckdb.DuckDBPyConnection,
    bronze_path: str | Path,
    old_version: int,
    new_version: int,
    reason: str,
) -> None:
    """Write down why a file was read a second time."""
    conn.execute(
        """
        INSERT INTO parse_corrections
            (feed_id, bronze_path, old_version, new_version, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        [FEED_ID, paths.relative_to_repo(bronze_path), old_version, new_version, reason],
    )


def run(
    conn: duckdb.DuckDBPyConnection,
    received_at: datetime | None = None,
    observation_start: str = DEFAULT_START,
    bronze_path: str | Path | None = None,
    reason: str | None = None,
) -> RunResult:
    """Do one run of this feed and report what happened.

    Same two modes and the same fixed step order as every other ingestor: open
    the run, fetch, bronze before parse, parse purely, insert in one
    transaction, close the run. Never raises for a feed failure — it is recorded
    and returned.
    """
    if received_at is None:
        received_at = clock.utc_now()

    replaying = bronze_path is not None
    parse_version = next_parse_version(conn, bronze_path) if replaying else 1
    if replaying and parse_version > 1 and not reason:
        raise ValueError(
            f"{bronze_path} has already been loaded, so re-reading it is a parser "
            f"correction: pass reason=... saying what the parser got wrong"
        )

    stored_path: str | None = None
    envelope: dict | None = None
    path: Path | None = None
    rows: list[tuple] = []

    if replaying:
        path = Path(bronze_path)
        stored_path = paths.relative_to_repo(path)
        try:
            envelope = read_envelope(path)
            received_at = datetime.fromisoformat(envelope["received_at"])
        except ControlroomError as exc:
            log.error("%s", exc)
            run_id = start_run(conn, FEED_ID, received_at)
            return finish_run(conn, run_id, "failed", bronze_path=stored_path, error=str(exc))

    run_id = start_run(conn, FEED_ID, received_at)

    try:
        if not replaying:
            payload = fetch(observation_start, received_at)
            path = write_bronze(FEED_ID, received_at, payload)  # disk first, always
            stored_path = paths.relative_to_repo(path)
            envelope = json.loads(payload)

        validate(envelope, stored_path)
        rows = parse(envelope, path, parse_version)
        inserted = store(conn, rows)

        if replaying and parse_version > 1:
            record_correction(conn, path, parse_version - 1, parse_version, reason)

    except ControlroomError as exc:
        log.error("%s", exc)
        return finish_run(
            conn, run_id, "failed", rows_fetched=len(rows),
            bronze_path=stored_path, error=str(exc),
        )

    return finish_run(
        conn, run_id, "ok", rows_fetched=len(rows), rows_inserted=inserted,
        bronze_path=stored_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch US crude stocks from the EIA.")
    parser.add_argument("--reparse", metavar="FILE",
                        help="re-read a bronze file instead of fetching from the EIA")
    parser.add_argument("--reason", metavar="TEXT",
                        help="what the old parser got wrong; required when re-reading "
                             "a file whose rows are already stored")
    parser.add_argument("--start", default=DEFAULT_START, metavar="YYYY-MM-DD",
                        help=f"earliest week to ask for (default {DEFAULT_START})")
    args = parser.parse_args()

    if not settings.db_path.exists():
        raise SystemExit(
            f"{settings.db_path} does not exist. Build it first:\n"
            f"    uv run python db/init.py"
        )

    conn = duckdb.connect(str(settings.db_path))
    try:
        result = run(conn, observation_start=args.start,
                     bronze_path=args.reparse, reason=args.reason)
        print(result.summary())
        if result.status == "failed":
            raise SystemExit(1)

        span = conn.execute(
            """
            SELECT min(period_start), max(period_start), count(*)
            FROM observations WHERE feed_id = ? AND received_at = ?
            """,
            [FEED_ID, result.received_at],
        ).fetchone()
        if span[0] is not None:
            print(f"  {SERIES_ID:<24} {span[0]} to {span[1]}  ({span[2]} weeks, {UNIT})")

        revisions = conn.execute(
            """
            SELECT count(*) FROM (
                SELECT period_start FROM observations
                WHERE feed_id = ? GROUP BY period_start
                HAVING count(DISTINCT value) > 1
            )
            """,
            [FEED_ID],
        ).fetchone()[0]
        # The whole reason this feed exists in v0: watching a published number
        # change after the fact.
        print(f"  {revisions} week(s) where a later pull disagreed with an earlier one")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
