"""Changes to the shape of an existing database, applied once and in order.

A new database gets the current `db/schema.sql` and needs nothing from here.
This file exists for a database that already holds data: `CREATE TABLE IF NOT
EXISTS` quietly leaves an old table alone, so without a migration an older
database would keep its old columns while the views expect new ones — and the
failure would come later, somewhere confusing.

Every migration here must be safe to run twice (it checks first and does
nothing if already applied) and must never lose a row.
"""

import duckdb

from core.logging import get_logger

log = get_logger(__name__)

# The columns of `observations` in the order schema.sql declares them, minus
# parse_version. Listed so the copy below is explicit rather than relying on
# column order matching up.
_OBSERVATION_COLUMNS = (
    "feed_id, series_id, entity_id, period_start, period_end, "
    "value, unit, received_at, source_asof, bronze_path"
)


def _table_exists(conn: duckdb.DuckDBPyConnection, name: str) -> bool:
    return bool(
        conn.execute(
            "SELECT count(*) FROM duckdb_tables() WHERE table_name = ?", [name]
        ).fetchone()[0]
    )


def _has_column(conn: duckdb.DuckDBPyConnection, table: str, column: str) -> bool:
    return bool(
        conn.execute(
            "SELECT count(*) FROM duckdb_columns() WHERE table_name = ? AND column_name = ?",
            [table, column],
        ).fetchone()[0]
    )


def add_parse_version(conn: duckdb.DuckDBPyConnection, schema_sql: str) -> int:
    """Give an older `observations` table its `parse_version` column.

    Returns the number of rows carried across; 0 if there was nothing to do.

    Why this is a rebuild and not one `ALTER TABLE`: `parse_version` is part of
    the primary key, and a primary key cannot be altered in place. So the old
    table is renamed, `schema.sql` builds the new one, every row is copied over
    as `parse_version = 1` — they were all produced by the first parser — and
    only then is the old table dropped. It all happens in one transaction, so an
    interruption leaves the database exactly as it was.

    Nothing is lost and nothing is changed: the same rows come out the other
    side with one extra column whose value says "this is the first reading of
    that payload", which is true of every row written before today.
    """
    if not _table_exists(conn, "observations"):
        return 0  # a brand-new database: schema.sql will build it correctly
    if _has_column(conn, "observations", "parse_version"):
        return 0  # already migrated

    before = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    log.info("migrating observations to parse_version (%d rows)", before)

    conn.execute("BEGIN TRANSACTION")
    try:
        # The views read `observations`, so they have to go before it is renamed.
        # schema.sql re-creates all three a moment later.
        for view in ("observations_explore", "observations_holdout", "observations_latest"):
            conn.execute(f"DROP VIEW IF EXISTS {view}")

        conn.execute("ALTER TABLE observations RENAME TO observations_pre_parse_version")
        conn.execute(schema_sql)  # builds the new observations, and the views
        conn.execute(
            f"""
            INSERT INTO observations ({_OBSERVATION_COLUMNS}, parse_version)
            SELECT {_OBSERVATION_COLUMNS}, 1 FROM observations_pre_parse_version
            """
        )

        after = conn.execute("SELECT count(*) FROM observations").fetchone()[0]
        if after != before:
            raise RuntimeError(
                f"migration would have changed the row count ({before} -> {after}); "
                f"nothing has been written"
            )

        conn.execute("DROP TABLE observations_pre_parse_version")
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise

    log.info("migrated %d rows to parse_version = 1", after)
    return after


def run_all(conn: duckdb.DuckDBPyConnection, schema_sql: str) -> None:
    """Apply every migration that this database still needs. Safe to re-run."""
    add_parse_version(conn, schema_sql)
