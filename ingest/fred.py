"""Fetch Brent crude and the OVX volatility index from FRED into `observations`.

An "ingestor" is one small program that pulls one feed and stores it. This is the
FRED one. FRED is the St. Louis Federal Reserve's free public data service; we
take two daily series from it:

    DCOILBRENTEU  the Brent crude oil spot price, in US dollars per barrel
    OVXCLS        the CBOE crude oil volatility index, a number with no unit
                  that goes up when traders expect the oil price to swing about

It does four things, in this order, and the order matters:

    1. asks FRED for both series
    2. writes FRED's untouched reply to a file under data/bronze/ BEFORE
       reading it — so if step 3 has a bug, the data is still on disk and can
       be re-read once the bug is fixed, without asking FRED again
    3. turns that reply into rows
    4. adds the rows to the database, skipping any that are already there

Run it with:  uv run python -m ingest.fred
"""

import json
import os
from datetime import date, datetime
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
# Our names are short and stable; FRED's are theirs to change.
SERIES = {
    "DCOILBRENTEU": ("brent_spot", "usd_per_bbl"),
    "OVXCLS": ("ovx", "index"),
}

# Why not the full history: split_mask only covers ISO weeks 2015-2030, and
# observations_explore joins against it, so anything older would be stored and
# then never displayed. See docs/DECISIONS.md, 2026-09-05.
DEFAULT_START = "2015-01-01"


def fetch(observation_start: str) -> dict[str, dict]:
    """Ask FRED for each series and return its replies, unmodified.

    Returns a dictionary like {'DCOILBRENTEU': <whatever FRED sent>, ...}.
    Nothing is interpreted here. If FRED returns an error status, this raises
    and the run stops before anything is written.
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

    payloads = {}
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
        payloads[fred_series] = response.json()
    return payloads


def write_bronze(payloads: dict[str, dict], received_at: datetime) -> Path:
    """Save FRED's untouched replies to disk and return where they went.

    "Bronze" is the raw layer: files exactly as the source sent them, never
    edited, never deleted. This is the cheapest insurance in the system.

    The filename is the fetch time. Colons are not allowed in filenames on
    Windows, so they become hyphens.
    """
    folder = REPO_ROOT / "data" / "bronze" / FEED_ID
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{received_at.isoformat().replace(':', '-')}.json"
    path.write_text(json.dumps(payloads, indent=2))
    return path


def parse(
    payloads: dict[str, dict], received_at: datetime, bronze_path: Path
) -> list[tuple]:
    """Turn FRED's replies into rows shaped like the `observations` table."""
    rows = []
    for fred_series, payload in payloads.items():
        series_id, unit = SERIES[fred_series]

        # FRED's realtime_start is the day IT last refreshed this series — not
        # today, and not the same for both series. It goes in source_asof.
        # received_at is our own clock and must stay that way; putting FRED's
        # date there would break re-runs. See docs/feeds/fred.md.
        source_asof = datetime.fromisoformat(payload["realtime_start"])

        for observation in payload["observations"]:
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
                str(bronze_path.relative_to(REPO_ROOT)),
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

    payloads = fetch(observation_start)
    bronze_path = write_bronze(payloads, received_at)  # disk first, always
    rows = parse(payloads, received_at, bronze_path)

    register_feed(conn)
    before = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    # INSERT OR IGNORE: if a row with this exact key is already there, skip it
    # silently. The key includes received_at, so this only ever collides with a
    # re-run at the identical timestamp.
    conn.executemany(
        "INSERT OR IGNORE INTO observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    after = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    return after - before


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(
            f"{DB_PATH} does not exist. Build it first:\n"
            f"    uv run python db/init.py"
        )
    conn = duckdb.connect(str(DB_PATH))
    try:
        received_at = datetime.now()
        inserted = run(conn, received_at=received_at)
        total = conn.execute(
            "SELECT count(*) FROM observations WHERE feed_id = ?", [FEED_ID]
        ).fetchone()[0]
        print(f"{FEED_ID}: added {inserted} rows at {received_at:%Y-%m-%d %H:%M:%S}")
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
