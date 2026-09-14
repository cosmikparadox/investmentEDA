"""Run every feed, one after another. This is what `make ingest` calls.

    uv run python -m ingest

Each feed is independent, so one being down must not stop the others: a failure
is recorded in `ingest_runs`, printed in the summary table, and the command
exits 1 at the end so a person — or later a scheduler — can tell something went
wrong without reading the log (PRD FR-07).

The list of feeds below is written out by hand on purpose. There is no
discovery, no registry, no plugin mechanism: adding a feed means writing
`ingest/<name>.py` and adding one line here, which is easy to read and
impossible to get wrong by accident. See CLAUDE.md on what is forbidden.
"""

import sys

import duckdb

from core.config import settings
from core.logging import get_logger
from ingest import eia, fred, portwatch
from ingest.runs import RunResult

FEEDS = (fred, eia, portwatch)

log = get_logger(__name__)


def run_all(conn: duckdb.DuckDBPyConnection) -> list[RunResult]:
    """Run every feed in order and collect the results. Never stops early."""
    results = []
    for feed in FEEDS:
        result = feed.run(conn)
        results.append(result)
        if result.status == "failed":
            # Keep going. The next feed has nothing to do with this one.
            log.warning("%s failed; continuing with the rest", result.feed_id)
    return results


def print_table(results: list[RunResult]) -> None:
    """One line per feed: what it did, or why it did not."""
    print(f"\n{'feed':<20} {'status':<8} {'fetched':>8} {'new':>8} {'seconds':>8}")
    print("-" * 56)
    for result in results:
        print(
            f"{result.feed_id:<20} {result.status:<8} {result.rows_fetched:>8} "
            f"{result.rows_inserted:>8} {result.duration_s:>8.1f}"
        )
    for result in results:
        if result.error:
            print(f"\n{result.feed_id}: {result.error}")


def main() -> None:
    if not settings.db_path.exists():
        raise SystemExit(
            f"{settings.db_path} does not exist. Build it first:\n"
            f"    make init"
        )

    conn = duckdb.connect(str(settings.db_path))
    try:
        results = run_all(conn)
        print_table(results)

        total = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
        vintages = conn.execute(
            "SELECT count(DISTINCT received_at) FROM observations"
        ).fetchone()[0]
        print(f"\n{total} rows in observations across {vintages} vintages.")
    finally:
        conn.close()

    # Exit 1 if anything failed, so `make ingest` reports a failure rather than
    # looking like it worked.
    if any(result.status == "failed" for result in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
