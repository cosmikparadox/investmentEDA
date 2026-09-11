"""Create the DuckDB database and put the fixed reference data into it.

Run this once to build the database, and again any time you want to be sure the
tables and views match db/schema.sql. It is safe to run repeatedly: it only ever
creates missing objects and inserts missing reference rows. It never touches the
data an ingestor has written into `observations`.

What it does, in order:
  1. makes sure data/ and data/bronze/ exist
  2. opens (creating if needed) data/controlroom.duckdb
  3. runs db/schema.sql          -> the tables and views
  4. loads db/split_mask.csv     -> the committed explore/holdout split
  5. runs db/seed_entities.sql   -> the three v0 entities and their aliases
  6. prints what is in there now

Run with:  uv run python db/init.py
"""

from pathlib import Path

import duckdb

# Paths are worked out from this file's location, so the script runs correctly
# no matter which directory you call it from.
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = REPO_ROOT / "data"
DB_PATH = DB_DIR / "controlroom.duckdb"
BRONZE_DIR = DB_DIR / "bronze"

SCHEMA_SQL = Path(__file__).parent / "schema.sql"
SEED_SQL = Path(__file__).parent / "seed_entities.sql"
SPLIT_CSV = Path(__file__).parent / "split_mask.csv"


def load_split_mask(conn: duckdb.DuckDBPyConnection, csv_path: Path) -> None:
    """Copy db/split_mask.csv into the split_mask table.

    INSERT OR IGNORE means: if a row with that iso_week is already there, skip it.
    So re-running changes nothing, and the split in the database always matches
    the committed CSV.
    """
    if not csv_path.exists():
        raise SystemExit(
            f"{csv_path} is missing. Generate it once with:\n"
            f"    uv run python db/make_split.py"
        )
    conn.execute(
        """
        INSERT OR IGNORE INTO split_mask (iso_week, split)
        SELECT iso_week, split
        FROM read_csv(?, header = true, columns = {'iso_week': 'TEXT', 'split': 'TEXT'})
        """,
        [str(csv_path)],
    )


def main() -> None:
    DB_DIR.mkdir(exist_ok=True)
    BRONZE_DIR.mkdir(exist_ok=True)

    # connect() creates the database file if it does not exist yet.
    conn = duckdb.connect(str(DB_PATH))
    try:
        conn.execute(SCHEMA_SQL.read_text())
        load_split_mask(conn, SPLIT_CSV)
        conn.execute(SEED_SQL.read_text())

        # A quick read-back, so running this always tells you the true state.
        weeks, holdout = conn.execute(
            "SELECT count(*), count(*) FILTER (WHERE split = 'holdout') FROM split_mask"
        ).fetchone()
        entities = conn.execute("SELECT count(*) FROM entity_registry").fetchone()[0]
        aliases = conn.execute("SELECT count(*) FROM entity_alias").fetchone()[0]
        feeds = conn.execute("SELECT count(*) FROM feed_registry").fetchone()[0]
        observations = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
        notes = conn.execute("SELECT count(*) FROM observation_log").fetchone()[0]
        runs = conn.execute("SELECT count(*) FROM ingest_runs").fetchone()[0]
    finally:
        conn.close()

    print(f"Database ready: {DB_PATH}")
    print(f"  split_mask       {weeks:>6} ISO weeks ({holdout} holdout)")
    print(f"  entity_registry  {entities:>6} entities, {aliases} aliases")
    print(f"  feed_registry    {feeds:>6} feeds")
    print(f"  observations     {observations:>6} rows")
    print(f"  observation_log  {notes:>6} notes")
    print(f"  ingest_runs      {runs:>6} runs")


if __name__ == "__main__":
    main()
