"""Fetch Brent crude and the OVX volatility index from FRED into `observations`.

An "ingestor" is one small program that pulls one feed and stores it. This is the
FRED one. FRED is the St. Louis Federal Reserve's free public data service; we
take two daily series from it:

    DCOILBRENTEU  the Brent crude oil spot price, in US dollars per barrel
    OVXCLS        the CBOE crude oil volatility index, a number with no unit
                  that goes up when traders expect the oil price to swing about

It does five things, in this order, and the order matters:

    1. asks FRED for both series
    2. writes FRED's reply to a file under data/bronze/ BEFORE reading it, byte
       for byte, so a bug in step 4 cannot lose the data
    3. checks the reply looks like what we asked for
    4. turns it into rows
    5. adds the rows, skipping any already there

Two ways to run it:

    uv run python -m ingest.fred                    fetch from FRED and store
    uv run python -m ingest.fred --reparse FILE     re-read a bronze file instead

The second one is the whole reason bronze exists: if the parsing turns out to be
wrong, you fix it and re-read the files you already have, without going back to
FRED and without needing them to still be serving that data.
"""

import argparse
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb
import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "controlroom.duckdb"

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


class BadPayload(Exception):
    """FRED sent something we did not expect. Stop before storing it."""


def fetch(observation_start: str, received_at: datetime) -> dict:
    """Ask FRED for each series and wrap the replies, verbatim, in an envelope.

    The envelope is what gets written to bronze. It holds each reply as the exact
    text FRED sent — not re-formatted, not re-ordered — plus enough context to
    understand the file on its own in two years: when we asked, what we asked
    for, and what came back.

    The API key is deliberately NOT recorded. Bronze files are data, and a
    secret in a data file is a secret you will forget you wrote down.
    """
    load_dotenv(REPO_ROOT / ".env")  # a real environment variable wins over .env
    try:
        api_key = os.environ["FRED_API_KEY"]
    except KeyError:
        raise SystemExit(
            "FRED_API_KEY is not set. Put it in .env (see .env.example), or in "
            "your cloud environment's variables. Free key: "
            "https://fredaccount.stlouisfed.org/apikey"
        )

    responses = {}
    for fred_series in SERIES:
        response = httpx.get(
            ENDPOINT,
            params={
                "series_id": fred_series,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": observation_start,
            },
            timeout=30,
        )
        response.raise_for_status()  # stop on 4xx/5xx rather than store rubbish
        responses[fred_series] = {
            "status": response.status_code,
            "body": response.text,  # verbatim, exactly as it came off the wire
        }

    return {
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


def write_bronze(envelope: dict) -> Path:
    """Save the envelope to disk and return where it went.

    "Bronze" is the raw layer: what the source sent, never edited, never
    deleted. This is the cheapest insurance in the whole system.

    The filename is the fetch time. Colons are not allowed in filenames on
    Windows, so they become hyphens.
    """
    folder = REPO_ROOT / "data" / "bronze" / FEED_ID
    folder.mkdir(parents=True, exist_ok=True)
    stamp = envelope["received_at"].replace(":", "-")
    path = folder / f"{stamp}.json"
    path.write_text(json.dumps(envelope, indent=2))
    return path


def read_bronze(path: Path) -> dict:
    """Load an envelope written earlier. The other half of write_bronze."""
    envelope = json.loads(path.read_text())
    version = envelope.get("envelope_version")
    if version != ENVELOPE_VERSION:
        raise BadPayload(
            f"{path} is a version {version!r} bronze file; this code reads "
            f"version {ENVELOPE_VERSION}. Files written before 2026-09-05 used "
            f"an older shape — delete data/ and re-run db/init.py then this "
            f"ingestor, or write a converter if the history matters."
        )
    return envelope


def validate(envelope: dict) -> None:
    """Check the reply is the shape we expect, before any of it is stored.

    Deliberately checks structure and not plausibility. A rule like "an oil
    price must be positive" would have rejected April 2020, when WTI genuinely
    traded below zero. Refusing real data because it is surprising is worse
    than storing it.
    """
    requested_start = date.fromisoformat(envelope["request"]["observation_start"])
    # A day of slack, because FRED's clock and ours are in different time zones.
    latest_sane = date.today() + timedelta(days=1)

    for fred_series in SERIES:
        if fred_series not in envelope["responses"]:
            raise BadPayload(f"{fred_series}: missing from the reply entirely")

        body = json.loads(envelope["responses"][fred_series]["body"])

        if "observations" not in body:
            error = body.get("error_message", "no 'observations' key")
            raise BadPayload(f"{fred_series}: {error}")
        if not body["observations"]:
            raise BadPayload(f"{fred_series}: zero observations returned")
        try:
            date.fromisoformat(body["realtime_start"])
        except (KeyError, ValueError) as exc:
            raise BadPayload(f"{fred_series}: unusable realtime_start ({exc})")

        seen = set()
        for observation in body["observations"]:
            try:
                period = date.fromisoformat(observation["date"])
            except (KeyError, ValueError) as exc:
                raise BadPayload(f"{fred_series}: unusable date ({exc})")
            if period in seen:
                raise BadPayload(f"{fred_series}: {period} appears twice")
            seen.add(period)
            if not requested_start <= period <= latest_sane:
                raise BadPayload(
                    f"{fred_series}: {period} is outside the window we asked "
                    f"for ({requested_start} to {latest_sane})"
                )
            raw = observation.get("value")
            if raw != "." :
                try:
                    float(raw)
                except (TypeError, ValueError):
                    raise BadPayload(f"{fred_series}: {period} value {raw!r}")


def parse(envelope: dict, bronze_path: Path) -> list[tuple]:
    """Turn a bronze envelope into rows shaped like the `observations` table.

    Takes the envelope rather than a live response, so re-reading an old file
    and fetching fresh data go down exactly the same code path. Touches no
    network and no database, which is what makes it straightforward to test.
    """
    received_at = datetime.fromisoformat(envelope["received_at"])

    # Store the path relative to the repo when it is inside it, so the value
    # means the same thing on any machine. A file somewhere else — someone
    # re-parsing an archived copy — is recorded as given rather than refused.
    try:
        recorded_path = str(bronze_path.relative_to(REPO_ROOT))
    except ValueError:
        recorded_path = str(bronze_path)

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


def store(conn: duckdb.DuckDBPyConnection, rows: list[tuple]) -> int:
    """Add rows, skip any already present, and report how many were new."""
    register_feed(conn)
    before = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    # INSERT OR IGNORE: if a row with this exact key is already there, skip it
    # silently. The key includes received_at, so this only ever collides with a
    # re-run at the identical timestamp — or with a re-parse of a bronze file
    # already loaded, which is why --reparse warns instead of pretending.
    # Columns are named rather than positional, so `parse_version` takes its
    # default of 1 — this is the first reading of the payload. A re-read after a
    # parser fix inserts version 2 explicitly; see docs/QUESTIONS.md Q1.
    conn.executemany(
        """
        INSERT OR IGNORE INTO observations
            (feed_id, series_id, entity_id, period_start, period_end,
             value, unit, received_at, source_asof, bronze_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    after = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    return after - before


def run(
    conn: duckdb.DuckDBPyConnection,
    received_at: datetime | None = None,
    observation_start: str = DEFAULT_START,
) -> int:
    """Do one fetch-and-store, and return how many rows were added.

    Safe to run as often as you like. Running it twice in the same second adds
    nothing the second time; running it tomorrow adds a fresh copy of every
    value, stamped with tomorrow's date. Nothing is ever changed or removed.
    """
    if received_at is None:
        received_at = datetime.now()

    envelope = fetch(observation_start, received_at)
    bronze_path = write_bronze(envelope)  # disk first, always
    validate(envelope)                    # only now do we look at it
    return store(conn, parse(envelope, bronze_path))


def run_from_bronze(conn: duckdb.DuckDBPyConnection, path: Path) -> tuple[int, int]:
    """Re-read a bronze file into the database. Returns (added, already there).

    Use this after fixing a parsing bug. The rows keep the original file's
    `received_at`, because that genuinely is when the data arrived — inventing
    a new one would claim a vintage that never happened.

    Consequence worth understanding: if those rows are already loaded, this adds
    nothing, because the key already exists. Correcting a vintage that was
    stored *wrongly* is a separate and deliberate operation — it means deleting
    rows, which rule 1 forbids without a decision. See docs/QUESTIONS.md.
    """
    envelope = read_bronze(path)
    validate(envelope)
    rows = parse(envelope, path)
    added = store(conn, rows)
    return added, len(rows) - added


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Brent and OVX from FRED.")
    parser.add_argument(
        "--reparse",
        metavar="FILE",
        help="re-read a bronze file instead of fetching from FRED",
    )
    parser.add_argument(
        "--start",
        default=DEFAULT_START,
        metavar="YYYY-MM-DD",
        help=f"earliest period to ask for (default {DEFAULT_START})",
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(
            f"{DB_PATH} does not exist. Build it first:\n"
            f"    uv run python db/init.py"
        )

    conn = duckdb.connect(str(DB_PATH))
    try:
        if args.reparse:
            path = Path(args.reparse).resolve()
            added, skipped = run_from_bronze(conn, path)
            print(f"{FEED_ID}: re-read {path.name}")
            print(f"  {added} rows added, {skipped} already present")
            if added == 0 and skipped:
                print("  (nothing changed — that vintage is already loaded)")
            return

        received_at = datetime.now()
        added = run(conn, received_at=received_at, observation_start=args.start)
        total = conn.execute(
            "SELECT count(*) FROM observations WHERE feed_id = ?", [FEED_ID]
        ).fetchone()[0]
        print(f"{FEED_ID}: added {added} rows at {received_at:%Y-%m-%d %H:%M:%S}")
        print(f"  {total} rows in total across all runs of this feed")
        for series_id, unit in SERIES.values():
            row = conn.execute(
                """
                SELECT min(period_start), max(period_start),
                       count(*) FILTER (WHERE value IS NULL)
                FROM observations
                WHERE feed_id = ? AND series_id = ? AND received_at = ?
                """,
                [FEED_ID, series_id, received_at],
            ).fetchone()
            print(f"  {series_id:<12} {row[0]} to {row[1]}  ({row[2]} empty days, {unit})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
