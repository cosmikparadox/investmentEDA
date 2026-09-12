"""Fetch Brent crude and the OVX volatility index from FRED into `observations`.

An "ingestor" is one small program that pulls one feed and stores it. This is the
FRED one. FRED is the St. Louis Federal Reserve's free public data service; we
take two daily series from it:

    DCOILBRENTEU  the Brent crude oil spot price, in US dollars per barrel
    OVXCLS        the CBOE crude oil volatility index, a number with no unit
                  that goes up when traders expect the oil price to swing about

One run does these things, in this order, and the order is fixed by
ARCHITECTURE.md §3.1 — it is not a style choice:

    1. open a run in `ingest_runs`, so an attempt that dies leaves evidence
    2. ask FRED for both series
    3. write FRED's reply to data/bronze/ BEFORE reading it, byte for byte, so
       a bug in step 5 cannot lose the data
    4. check the reply is the shape we expect
    5. turn it into rows — a pure function, no clock and no database
    6. insert them in one transaction, skipping any already there
    7. close the run, recording what happened

Three ways to run it:

    uv run python -m ingest.fred                     fetch from FRED and store
    uv run python -m ingest.fred --reparse FILE --reason "..."
                                                     re-read a file we already have
    uv run python -m ingest.fred --start 2020-01-01  ask for a different window

The second one is the whole reason bronze exists. If the parsing turns out to
have been wrong, you fix it and re-read the files already on disk — no second
request to FRED, and no need for them to still be serving that history. The
re-read keeps the file's original `received_at`, because that really is when the
data arrived, and stores the corrected rows under the next `parse_version`. The
wrong rows stay exactly where they are, as evidence of what we believed. See
docs/QUESTIONS.md Q1.
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

FEED_ID = "fred_brent_ovx"
ENDPOINT = "https://api.stlouisfed.org/fred/series/observations"

# The one entity these numbers are about. A price benchmark, not a place.
# 'benchmark:brent' is a canonical ID from entity_registry — see rule 3 in
# CLAUDE.md: names are aliases, IDs are keys.
ENTITY_ID = "benchmark:brent"

# FRED's name for a series -> (our name for it, what it is measured in).
SERIES = {
    "DCOILBRENTEU": ("brent_spot", "usd_per_bbl"),
    "OVXCLS": ("ovx", "index"),
}

# Why not the full history: split_mask only covers ISO weeks 2015-2030, and
# observations_explore joins against it, so anything older would be stored and
# then never displayed. See docs/DECISIONS.md, 2026-09-05.
DEFAULT_START = "2015-01-01"

# Bumped only if the shape of a bronze file changes. Old files keep their old
# number, so a reader can always tell what it is holding.
ENVELOPE_VERSION = 1

log = get_logger(__name__, FEED_ID)


def fetch(observation_start: str, received_at: datetime) -> bytes:
    """Ask FRED for each series and wrap the replies, verbatim, in an envelope.

    Returns the bytes to write to bronze. The envelope holds each reply as the
    exact text FRED sent — not re-formatted, not re-ordered — plus enough
    context to understand the file on its own in two years: when we asked, what
    we asked for, and what came back.

    The API key is deliberately NOT recorded. Bronze files are data, and a
    secret in a data file is a secret you will forget you wrote down.

    Raises FeedError (via core.http) if FRED cannot be reached or refuses us.
    """
    key = api_key("FRED_API_KEY")

    responses = {}
    for fred_series in SERIES:
        reply = get(
            FEED_ID,
            ENDPOINT,
            params={
                "series_id": fred_series,
                "api_key": key,
                "file_type": "json",
                "observation_start": observation_start,
            },
        )
        responses[fred_series] = {
            "status": reply.status_code,
            "body": reply.text,  # verbatim, exactly as it came off the wire
        }
        log.debug("%s: %d characters", fred_series, len(reply.text))

    envelope = {
        "envelope_version": ENVELOPE_VERSION,
        "feed_id": FEED_ID,
        "received_at": received_at.isoformat(),
        "endpoint": ENDPOINT,
        "request": {
            "series": list(SERIES),
            "observation_start": observation_start,
            "file_type": "json",
        },
        "responses": responses,
    }
    return json.dumps(envelope, indent=2).encode()


def read_envelope(path: str | Path) -> dict:
    """Read a bronze file back and check it is a shape this code understands.

    `ingest.bronze.read_bronze` returns the raw bytes; turning them into an
    envelope is this feed's business, because only this module knows what its
    own files look like.
    """
    payload = read_bronze(path)
    try:
        envelope = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ParseError(
            FEED_ID, f"not valid JSON ({exc})", bronze_path=str(path)
        ) from exc

    version = envelope.get("envelope_version")
    if version != ENVELOPE_VERSION:
        raise ParseError(
            FEED_ID,
            f"this is a version {version!r} bronze file; this code reads version "
            f"{ENVELOPE_VERSION}. Files written before 2026-09-05 used an older "
            f"shape — write a converter if that history matters",
            bronze_path=str(path),
            field="envelope_version",
        )
    return envelope


def validate(envelope: dict, bronze_path: str | Path | None = None) -> None:
    """Check the reply is the shape we expect, before any of it is stored.

    Deliberately checks structure and not plausibility. A rule like "an oil
    price must be positive" would have rejected April 2020, when WTI genuinely
    traded below zero. Refusing real data because it is surprising is worse
    than storing it.
    """
    where = str(bronze_path) if bronze_path else None

    def refuse(message: str, field: str | None = None, sample: str | None = None):
        raise ParseError(FEED_ID, message, bronze_path=where, field=field, sample=sample)

    requested_start = date.fromisoformat(envelope["request"]["observation_start"])
    # A day of slack, because FRED's clock and ours are in different time zones.
    latest_sane = date.today() + timedelta(days=1)

    for fred_series in SERIES:
        if fred_series not in envelope["responses"]:
            refuse(f"{fred_series}: missing from the reply entirely", field=fred_series)

        body = json.loads(envelope["responses"][fred_series]["body"])

        if "observations" not in body:
            error = body.get("error_message", "no 'observations' key")
            refuse(f"{fred_series}: {error}", field="observations")
        if not body["observations"]:
            refuse(f"{fred_series}: zero observations returned", field="observations")
        try:
            date.fromisoformat(body["realtime_start"])
        except (KeyError, ValueError) as exc:
            refuse(f"{fred_series}: unusable realtime_start ({exc})", field="realtime_start")

        seen = set()
        for observation in body["observations"]:
            try:
                period = date.fromisoformat(observation["date"])
            except (KeyError, ValueError) as exc:
                refuse(f"{fred_series}: unusable date ({exc})", field="date")
            if period in seen:
                refuse(f"{fred_series}: {period} appears twice", field="date",
                       sample=str(period))
            seen.add(period)
            if not requested_start <= period <= latest_sane:
                refuse(
                    f"{fred_series}: {period} is outside the window we asked for "
                    f"({requested_start} to {latest_sane})",
                    field="date",
                    sample=str(period),
                )
            raw = observation.get("value")
            if raw != ".":
                try:
                    float(raw)
                except (TypeError, ValueError):
                    refuse(f"{fred_series}: {period} value {raw!r}", field="value",
                           sample=repr(raw))


def parse(
    envelope: dict,
    bronze_path: str | Path,
    parse_version: int = 1,
) -> list[tuple]:
    """Turn a bronze envelope into rows shaped like the `observations` table.

    A pure function: payload in, rows out. No network, no database, and no
    clock — `received_at` comes from the envelope, never from `now()`. That is
    what makes re-reading an old file and fetching fresh data go down exactly
    the same code path, and what makes this testable against a saved fixture.

    `parse_version` says which reading of the payload these rows are. 1 for a
    first read; 2 or more when a parser bug has been fixed and the file re-read.
    """
    received_at = datetime.fromisoformat(envelope["received_at"])
    recorded_path = paths.relative_to_repo(bronze_path)

    rows = []

    for fred_series, (series_id, unit) in SERIES.items():
        body = json.loads(envelope["responses"][fred_series]["body"])

        # FRED's realtime_start is the day IT last refreshed this series — not
        # today, and not the same for both series. It goes in source_asof.
        # received_at is our own clock and must stay that way; putting FRED's
        # date there would break re-runs. See docs/feeds/fred.md.
        source_asof = datetime.fromisoformat(body["realtime_start"])

        for observation in body["observations"]:
            raw = observation["value"]
            # FRED writes a missing number as the single character ".", on days
            # the market was shut. Store it as a real row with an empty value:
            # "nothing was published that day" is itself information, and
            # dropping the row would lose it.
            value = None if raw == "." else float(raw)
            period = date.fromisoformat(observation["date"])

            rows.append((
                FEED_ID,
                series_id,
                ENTITY_ID,
                period,          # period_start — the day this number is about
                period,          # period_end   — same, because it is daily data
                value,
                unit,
                received_at,     # the vintage: when WE had it
                source_asof,
                recorded_path,
                parse_version,
            ))
    return rows


def register_feed(conn: duckdb.DuckDBPyConnection) -> None:
    """Record what this feed is and where it really comes from.

    Rule 2 in CLAUDE.md: every feed says its upstream source in plain English,
    so that when two feeds agree you can tell whether that is genuine
    confirmation or the same source arriving twice. Details match
    docs/feeds/fred.md.
    """
    conn.execute(
        """
        INSERT OR IGNORE INTO feed_registry
            (feed_id, provider, upstream, cadence, endpoint, license_notes, added_on)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            FEED_ID,
            "FRED, St. Louis Fed",
            "ICE Brent settlement via EIA (DCOILBRENTEU); CBOE (OVXCLS), both via FRED",
            "daily",
            ENDPOINT,
            "DCOILBRENTEU public domain. OVXCLS is CBOE copyright: use, do not republish.",
            date.today(),
        ],
    )


def next_parse_version(conn: duckdb.DuckDBPyConnection, bronze_path: str | Path) -> int:
    """What the next reading of this file should be numbered.

    1 if the file has never been loaded, otherwise one past the highest version
    already stored for it. Looked up per file rather than per feed, because two
    files can be at different versions — only the one whose parse was wrong gets
    re-read.
    """
    highest = conn.execute(
        """
        SELECT coalesce(max(parse_version), 0) FROM observations
        WHERE feed_id = ? AND bronze_path = ?
        """,
        [FEED_ID, paths.relative_to_repo(bronze_path)],
    ).fetchone()[0]
    return int(highest) + 1


def store(conn: duckdb.DuckDBPyConnection, rows: list[tuple]) -> int:
    """Add rows in one transaction, skip any already present, report how many were new.

    One transaction (NFR-02): either every row of this run lands or none of them
    does. A half-written vintage would be indistinguishable from a day when the
    source published less than usual.
    """
    register_feed(conn)
    before = conn.execute("SELECT count(*) FROM observations").fetchone()[0]

    conn.execute("BEGIN TRANSACTION")
    try:
        # INSERT OR IGNORE: if a row with this exact key is already there, skip
        # it silently. The key includes received_at and parse_version, so this
        # only collides with a re-run at the identical timestamp, or a re-parse
        # that has already been stored.
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
    """Write down why a file was read a second time.

    Without this, a jump from parse_version 1 to 2 in `observations` is a
    mystery in six months' time.
    """
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

    Two modes:

      * normal — fetch from FRED, write the reply to bronze, parse, store.
        `received_at` defaults to now (UTC) and is our own clock; passing it
        explicitly is for tests.

      * replay — pass `bronze_path` and no request is made. The file is re-read
        and stored under the next `parse_version`, keeping the file's ORIGINAL
        `received_at`. If that file has been loaded before, this is a parser
        correction and `reason` is required, so the `parse_corrections` row can
        say what was wrong.

    Never raises for a feed failure: a source that is down, refuses us, or sends
    something unparseable is recorded in `ingest_runs` and returned as a failed
    RunResult. Programmer errors — a missing table, a bad argument — are left to
    crash, because they should be fixed rather than logged.
    """
    if received_at is None:
        received_at = clock.utc_now()

    replaying = bronze_path is not None
    parse_version = next_parse_version(conn, bronze_path) if replaying else 1
    if replaying and parse_version > 1 and not reason:
        raise ValueError(
            f"{bronze_path} has already been loaded, so re-reading it is a parser "
            f"correction: pass reason=... saying what the parser got wrong "
            f"(--reason on the command line)"
        )

    stored_path: str | None = None
    envelope: dict | None = None
    path: Path | None = None
    rows: list[tuple] = []

    if replaying:
        # Read the file before opening the run, because the file's own timestamp
        # is the vintage this run is writing, and `ingest_runs` should say so
        # rather than recording the wall clock. Inventing a new received_at
        # would claim a vintage that never happened.
        path = Path(bronze_path)
        stored_path = paths.relative_to_repo(path)
        try:
            envelope = read_envelope(path)
            received_at = datetime.fromisoformat(envelope["received_at"])
        except ControlroomError as exc:
            # An unreadable file is still an attempt, and still gets recorded —
            # stamped with our clock, since the file never told us its own.
            log.error("%s", exc)
            run_id = start_run(conn, FEED_ID, received_at)
            return finish_run(
                conn, run_id, "failed", bronze_path=stored_path, error=str(exc)
            )

    run_id = start_run(conn, FEED_ID, received_at)

    try:
        if not replaying:
            payload = fetch(observation_start, received_at)   # may raise FeedError
            path = write_bronze(FEED_ID, received_at, payload)  # disk first, always
            stored_path = paths.relative_to_repo(path)
            envelope = json.loads(payload)

        validate(envelope, stored_path)          # only now do we look at it
        rows = parse(envelope, path, parse_version)
        inserted = store(conn, rows)

        if replaying and parse_version > 1:
            record_correction(conn, path, parse_version - 1, parse_version, reason)

    except ControlroomError as exc:
        # A feed or storage failure: recorded, returned, not raised. The bronze
        # file, if one was written, is still on disk.
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
    parser = argparse.ArgumentParser(description="Fetch Brent and OVX from FRED.")
    parser.add_argument(
        "--reparse",
        metavar="FILE",
        help="re-read a bronze file we already have instead of fetching from FRED",
    )
    parser.add_argument(
        "--reason",
        metavar="TEXT",
        help="what the old parser got wrong; required when re-reading a file "
             "whose rows are already stored",
    )
    parser.add_argument(
        "--start",
        default=DEFAULT_START,
        metavar="YYYY-MM-DD",
        help=f"earliest period to ask for (default {DEFAULT_START})",
    )
    args = parser.parse_args()

    if not settings.db_path.exists():
        raise SystemExit(
            f"{settings.db_path} does not exist. Build it first:\n"
            f"    uv run python db/init.py"
        )

    conn = duckdb.connect(str(settings.db_path))
    try:
        result = run(
            conn,
            observation_start=args.start,
            bronze_path=args.reparse,
            reason=args.reason,
        )
        print(result.summary())

        if result.status == "failed":
            raise SystemExit(1)

        total = conn.execute(
            "SELECT count(*) FROM observations WHERE feed_id = ?", [FEED_ID]
        ).fetchone()[0]
        print(f"  run {result.received_at:%Y-%m-%d %H:%M:%S} UTC, "
              f"{total} rows in total across all runs of this feed")

        if result.rows_inserted == 0:
            print("  (nothing new — that vintage is already stored)")

        for series_id, unit in SERIES.values():
            row = conn.execute(
                """
                SELECT min(period_start), max(period_start),
                       count(*) FILTER (WHERE value IS NULL)
                FROM observations
                WHERE feed_id = ? AND series_id = ? AND received_at = ?
                """,
                [FEED_ID, series_id, result.received_at],
            ).fetchone()
            if row[0] is not None:
                print(f"  {series_id:<12} {row[0]} to {row[1]}  "
                      f"({row[2]} empty days, {unit})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
