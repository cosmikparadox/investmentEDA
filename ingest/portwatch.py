"""Fetch daily ship transits through the Strait of Hormuz into `observations`.

IMF PortWatch is a free service from the IMF and Oxford that turns satellite AIS
— the position beacons ships broadcast — into daily counts of vessels passing
the world's maritime chokepoints. We take one chokepoint:

    chokepoint6   the Strait of Hormuz, the narrow passage out of the Persian
                  Gulf that roughly a fifth of the world's oil moves through

and two numbers from it:

    n_total       all vessels counted that day
    n_tanker      the tankers among them

Two things to keep in mind about what these numbers are.

**They are modelled estimates, not a headcount.** PortWatch infers transits from
AIS tracks. AIS can be switched off, and it can be spoofed — and since February
2026 there has been heavy GPS jamming in the Gulf. The counts fell from roughly
85 a day before the crisis to single figures in late August 2026. Some of that
is real and some of it is ships going dark. This feed is the system's first
lesson in a number that measures the observer as much as the world.

**PortWatch backfills recent days silently**, with no way to ask what it said
last week. So, like the EIA feed, every pull is a snapshot stamped with our own
`received_at`, and the accumulated snapshots are the only record of what was
known when.

    uv run python -m ingest.portwatch
    uv run python -m ingest.portwatch --reparse FILE --reason "..."

Source: IMF PortWatch, https://portwatch.imf.org — attribution is required by
their terms, and is recorded in `feed_registry.license_notes`.
"""

import argparse
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb

from core import clock, paths
from core.config import settings
from core.errors import ControlroomError, ParseError, StorageError
from core.http import get
from core.logging import get_logger
from ingest.bronze import read_bronze, write_bronze
from ingest.runs import RunResult, finish_run, start_run

FEED_ID = "portwatch_hormuz"
ENDPOINT = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
    "Daily_Chokepoints_Data/FeatureServer/0/query"
)

# PortWatch's own id for the strait, and our canonical one. Rule 3: their id is
# an alias, ours is the key. Both are in db/seed_entities.sql.
PORT_ID = "chokepoint6"
ENTITY_ID = "chokepoint:hormuz"

# Their field name -> (our series name, what it is measured in).
SERIES = {
    "n_total": ("hormuz_transits_total", "vessels"),
    "n_tanker": ("hormuz_transits_tanker", "vessels"),
}

# split_mask covers ISO weeks 2015-2030. PortWatch's history starts 2019-01-01,
# well inside that, so we ask for everything and store what comes back.
DEFAULT_START = "2015-01-01"

# The layer's maxRecordCount, confirmed on a live call 2026-09-12. The server
# will not return more than this in one reply however much we ask for, so the
# only way to get the full history is to page.
PAGE_SIZE = 1000

ENVELOPE_VERSION = 1

log = get_logger(__name__, FEED_ID)


def fetch(observation_start: str, received_at: datetime) -> bytes:
    """Page through the whole chokepoint history and keep every reply verbatim.

    Ordered by ObjectId rather than by date: paging is only safe if the server
    sorts the rows the same way on every request, and ObjectId is the one field
    guaranteed to be unique and stable.

    `observation_start` is not sent to the server. Their spec warns that date
    filtering is unverified, so we ask for the lot — about 2,800 rows, which is
    three requests — and filter locally where we can see what we are doing.
    """
    pages: dict[str, dict] = {}
    offset = 0
    while True:
        reply = get(
            FEED_ID,
            ENDPOINT,
            params={
                "where": f"portid='{PORT_ID}'",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json",
                "orderByFields": "ObjectId ASC",
                "resultOffset": offset,
                "resultRecordCount": PAGE_SIZE,
            },
        )
        pages[f"page_{len(pages)}"] = {
            "status": reply.status_code,
            "offset": offset,
            "body": reply.text,  # verbatim, exactly as it came off the wire
        }

        body = json.loads(reply.text)
        features = body.get("features", [])
        offset += len(features)
        log.debug("page %d: %d rows so far", len(pages) - 1, offset)

        # exceededTransferLimit means "there are more where those came from".
        # The empty-page check stops a server that always says True from
        # spinning here for ever.
        if not body.get("exceededTransferLimit") or not features:
            break

    return json.dumps(
        {
            "envelope_version": ENVELOPE_VERSION,
            "feed_id": FEED_ID,
            "received_at": received_at.isoformat(),
            "endpoint": ENDPOINT,
            "request": {
                "portid": PORT_ID,
                "observation_start": observation_start,
                "page_size": PAGE_SIZE,
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


def features_of(envelope: dict) -> list[dict]:
    """Every feature's attributes, from every page, in the order they arrived."""
    collected = []
    for name in sorted(envelope["responses"], key=lambda n: int(n.split("_")[1])):
        body = json.loads(envelope["responses"][name]["body"])
        collected.extend(f.get("attributes", {}) for f in body.get("features", []))
    return collected


def to_date(raw: object) -> date:
    """Turn PortWatch's date field into a real date.

    Two shapes are accepted on purpose. The feed spec recorded epoch
    milliseconds, and a live call on 2026-09-12 returned 'YYYY-MM-DD' strings
    instead — ArcGIS serves its date-only fields either way depending on a
    server-side setting we do not control. Handling both means a flip does not
    silently break the ingestor; anything else is refused.
    """
    if isinstance(raw, str):
        return date.fromisoformat(raw)
    if isinstance(raw, (int, float)):
        # Epoch milliseconds, UTC. Their day boundary is UTC, not local.
        return datetime.fromtimestamp(raw / 1000, tz=UTC).date()
    raise ValueError(f"date is {type(raw).__name__}, expected a string or a number")


def validate(envelope: dict, bronze_path: str | Path | None = None) -> None:
    """Check the reply is the shape we expect, before any of it is stored.

    Structure, not plausibility — deliberately. Hormuz transits fell from about
    85 a day to single figures during 2026. A rule like "reject an 80% drop"
    would have thrown away the most important weeks in the series.
    """
    where = str(bronze_path) if bronze_path else None

    def refuse(message: str, field: str | None = None, sample: str | None = None):
        raise ParseError(FEED_ID, message, bronze_path=where, field=field, sample=sample)

    first_body = json.loads(envelope["responses"]["page_0"]["body"])
    if "error" in first_body:
        refuse(f"the server returned an error: {first_body['error']}", field="error")

    attributes = features_of(envelope)
    if not attributes:
        refuse("zero features returned", field="features")

    requested_start = date.fromisoformat(envelope["request"]["observation_start"])
    latest_sane = date.today() + timedelta(days=1)
    seen = set()

    for row in attributes:
        try:
            period = to_date(row.get("date"))
        except (ValueError, TypeError, OSError) as exc:
            refuse(f"unusable date ({exc})", field="date", sample=str(row.get("date"))[:100])

        if period in seen:
            refuse(f"{period} appears twice", field="date", sample=str(period))
        seen.add(period)

        if period > latest_sane:
            refuse(f"{period} is in the future", field="date", sample=str(period))
        if period < requested_start:
            refuse(
                f"{period} is before {requested_start}, which split_mask does not "
                f"cover — those rows would be stored and never displayed",
                field="date",
                sample=str(period),
            )

        # The query filters on portid, so a row for a different chokepoint means
        # the server stopped honouring the filter. Storing it would attach
        # another strait's traffic to Hormuz.
        portid = str(row.get("portid", "")).lower()
        if portid != PORT_ID:
            refuse(f"{period} is for portid {portid!r}, not {PORT_ID!r}",
                   field="portid", sample=repr(row.get("portid")))

        for field in SERIES:
            count = row.get(field)
            if count is not None and not isinstance(count, (int, float)):
                refuse(f"{period} {field} is {count!r}", field=field, sample=repr(count))


def parse(envelope: dict, bronze_path: str | Path, parse_version: int = 1) -> list[tuple]:
    """Turn a bronze envelope into rows shaped like the `observations` table.

    A pure function: no network, no database, no clock.

    `period_start` and `period_end` are the same day, because a transit count is
    a flow over one day — all the ships seen on that date.
    """
    received_at = datetime.fromisoformat(envelope["received_at"])
    recorded_path = paths.relative_to_repo(bronze_path)

    rows = []
    for attributes in features_of(envelope):
        period = to_date(attributes["date"])
        for field, (series_id, unit) in SERIES.items():
            count = attributes.get(field)
            # A day PortWatch has no count for stays a row with no value. "No
            # ships were counted" and "we have no count" are different facts and
            # the second one is worth keeping.
            value = None if count is None else float(count)

            rows.append((
                FEED_ID,
                series_id,
                ENTITY_ID,
                period,
                period,
                value,
                unit,
                received_at,
                # PortWatch does not publish when a row was last recomputed, and
                # it backfills silently, so we cannot claim to know.
                None,
                recorded_path,
                parse_version,
            ))
    return rows


def register_feed(conn: duckdb.DuckDBPyConnection) -> None:
    """Record what this feed is and where it really comes from (rule 2).

    The upstream line matters more here than anywhere: these counts are modelled
    from satellite AIS, so anyone comparing them with another AIS-derived feed is
    looking at the same underlying observations twice, not at confirmation.
    """
    conn.execute(
        """
        INSERT OR IGNORE INTO feed_registry
            (feed_id, provider, upstream, cadence, endpoint, license_notes, added_on)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            FEED_ID,
            "IMF PortWatch (IMF and Oxford)",
            "Satellite AIS vessel positions, turned into modelled daily transit "
            "estimates by IMF PortWatch. Not a headcount.",
            "weekly",  # they publish weekly; the rows themselves are daily
            ENDPOINT,
            "Source: IMF PortWatch, https://portwatch.imf.org. Attribution required. "
            "Bulk download of the whole site is prohibited; one chokepoint is fine.",
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

    Same two modes and the same fixed step order as every other ingestor. Never
    raises for a feed failure — it is recorded and returned.
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
    parser = argparse.ArgumentParser(
        description="Fetch Strait of Hormuz transit counts from IMF PortWatch."
    )
    parser.add_argument("--reparse", metavar="FILE",
                        help="re-read a bronze file instead of fetching from PortWatch")
    parser.add_argument("--reason", metavar="TEXT",
                        help="what the old parser got wrong; required when re-reading "
                             "a file whose rows are already stored")
    parser.add_argument("--start", default=DEFAULT_START, metavar="YYYY-MM-DD",
                        help=f"earliest date to keep (default {DEFAULT_START})")
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

        for series_id, unit in SERIES.values():
            row = conn.execute(
                """
                SELECT min(period_start), max(period_start), count(*),
                       count(*) FILTER (WHERE value IS NULL)
                FROM observations
                WHERE feed_id = ? AND series_id = ? AND received_at = ?
                """,
                [FEED_ID, series_id, result.received_at],
            ).fetchone()
            if row[0] is not None:
                print(f"  {series_id:<24} {row[0]} to {row[1]}  "
                      f"({row[2]} days, {row[3]} with no count, {unit})")

        recent = conn.execute(
            """
            SELECT avg(value) FROM observations
            WHERE feed_id = ? AND series_id = 'hormuz_transits_total'
              AND received_at = ? AND period_start >= ?
            """,
            [FEED_ID, result.received_at, date.today() - timedelta(days=30)],
        ).fetchone()[0]
        if recent is not None:
            print(f"  last 30 days averaged {recent:.1f} vessels a day "
                  f"(pre-2026 baseline was about 85 — see docs/feeds/portwatch.md)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
