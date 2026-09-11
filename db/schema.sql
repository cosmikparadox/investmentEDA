-- db/schema.sql
-- Every table and view in the v0 database, exactly as specified in docs/DESIGN.md.
-- Run by db/init.py. Safe to run more than once: nothing here drops or rewrites data.
--
-- Jargon, defined once:
--   "bitemporal" = every row carries two dates. What the number is ABOUT
--     (period_start) and when WE received it (received_at). Keeping both is what
--     lets us ask "what did we know on 12 March?" instead of only "what is true now?".
--   "vintage"    = one particular received_at. A revised value is a new vintage,
--     a new row, sitting alongside the old one. We never overwrite.
--   "view"       = a saved query that behaves like a table. It stores no data.
--
-- TIME ZONES — read this before writing any query that compares timestamps.
--   Every TIMESTAMP column in this database is UTC. They are stored "naive",
--   meaning the value carries no time zone marker: the convention is written
--   down here rather than in the column type, and applied everywhere. Code gets
--   the current time from core.clock.utc_now() and nowhere else.
--   The one exception is history. Rows written before 2026-09-11 were stamped
--   with the machine's local clock, which was British Summer Time (UTC+1). They
--   are an hour ahead of the convention and were deliberately left alone —
--   received_at is part of the primary key and of every bronze filename, so
--   rewriting them would mean a second migration touching files on disk to
--   correct a one-hour offset on daily and weekly data. docs/DECISIONS.md
--   records the exact run after which received_at is UTC, for anyone who ever
--   needs to subtract that hour.


-- ---------------------------------------------------------------------------
-- ingest_runs — the operational history. One row per attempt to fetch a feed,
-- written when the run starts and completed when it ends.
-- The first place to look when something is wrong: it says what ran, when, how
-- long it took, how many rows it added, and the error text if it failed.
-- Unlike `observations`, a run row IS updated — once, by its own run, to fill in
-- how it ended. Rule 1 is about never overwriting ingested data; this table is a
-- logbook of attempts, not data from a source.
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS ingest_runs_id_seq START 1;

CREATE TABLE IF NOT EXISTS ingest_runs (
    run_id        INTEGER PRIMARY KEY DEFAULT nextval('ingest_runs_id_seq'),
    feed_id       TEXT NOT NULL,
    received_at   TIMESTAMP NOT NULL,  -- the vintage this run was writing
    started_at    TIMESTAMP NOT NULL,
    finished_at   TIMESTAMP,           -- NULL while the run is still going
    status        TEXT NOT NULL,       -- 'running' | 'ok' | 'failed'
    rows_fetched  INTEGER,
    rows_inserted INTEGER,             -- after skipping rows already present
    bronze_path   TEXT,
    error         TEXT                 -- redacted, first 500 characters
);


-- ---------------------------------------------------------------------------
-- feed_registry — one row per ingestor. What it is and where it really comes from.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feed_registry (
    feed_id       TEXT PRIMARY KEY,
    provider      TEXT NOT NULL,
    upstream      TEXT NOT NULL,     -- plain text. Where does this REALLY come from.
    cadence       TEXT NOT NULL,     -- 'daily', 'weekly', 'monthly'
    endpoint      TEXT NOT NULL,
    license_notes TEXT,
    added_on      DATE NOT NULL
);


-- ---------------------------------------------------------------------------
-- entity_registry — the canonical things the data is about. IDs never change.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS entity_registry (
    entity_id     TEXT PRIMARY KEY,  -- canonical, never changes
    entity_type   TEXT NOT NULL,     -- 'chokepoint', 'country', 'benchmark', 'port', 'vessel', 'company'
    id_scheme     TEXT NOT NULL,     -- 'PORTWATCH', 'ISO3166A3', 'INTERNAL', 'UNLOCODE', 'IMO', 'LEI'
    display_name  TEXT NOT NULL,
    lat           DOUBLE,
    lon           DOUBLE,
    notes         TEXT
);

-- entity_alias — every name or code a source uses for an entity.
-- Names are aliases, never keys. Nothing joins on a name.
CREATE TABLE IF NOT EXISTS entity_alias (
    alias         TEXT NOT NULL,     -- any name or code a source uses
    scheme        TEXT NOT NULL,     -- where that alias comes from
    entity_id     TEXT NOT NULL REFERENCES entity_registry(entity_id),
    PRIMARY KEY (alias, scheme)
);


-- ---------------------------------------------------------------------------
-- observations — the actual asset. One long, narrow table for every number.
-- "Long" = one row per (series, period, vintage), not one column per series.
-- Looks wasteful; it is the correct shape for time series that get revised.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS observations (
    feed_id        TEXT NOT NULL,   -- which ingestor produced this
    series_id      TEXT NOT NULL,   -- e.g. 'hormuz_transits_total', 'brent_spot'
    entity_id      TEXT NOT NULL,   -- canonical ID from entity_registry
    period_start   DATE NOT NULL,   -- what period the value describes
    period_end     DATE NOT NULL,   -- same as period_start for daily data
    value          DOUBLE,          -- NULL allowed: a published gap is information
    unit           TEXT NOT NULL,   -- 'vessels', 'kbbl', 'usd_per_bbl', 'index'
    received_at    TIMESTAMP NOT NULL,  -- when WE fetched it. The vintage.
    source_asof    TIMESTAMP,       -- when the SOURCE says it published, if known
    bronze_path    TEXT NOT NULL,   -- which raw file this row came from
    parse_version  INTEGER NOT NULL DEFAULT 1,  -- which reading of that file this is
    PRIMARY KEY (feed_id, series_id, entity_id, period_start, received_at, parse_version)
);
-- parse_version, in plain terms: `received_at` says when the SOURCE's numbers
-- reached us, and `parse_version` says which attempt at READING them this row is.
-- If a parser turns out to have been wrong, we re-read the same bronze file with
-- the fixed parser, keep the original received_at — that really is when the data
-- arrived — and write the corrected rows as version 2. The wrong rows stay
-- forever as evidence of what we believed; nothing is updated and nothing is
-- deleted. A fresh fetch gets a new received_at; a re-read never does.
-- See docs/QUESTIONS.md Q1, answered 2026-09-11.


-- ---------------------------------------------------------------------------
-- parse_corrections — why a bronze file was ever read a second time.
-- Append-only, like everything else. One row each time a parser bug is fixed
-- and the affected files re-read: which file, which version replaced which, and
-- in plain words what was wrong. Without this, a jump from parse_version 1 to 2
-- in `observations` is a mystery in six months' time.
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS parse_corrections_id_seq START 1;

CREATE TABLE IF NOT EXISTS parse_corrections (
    correction_id INTEGER PRIMARY KEY DEFAULT nextval('parse_corrections_id_seq'),
    feed_id       TEXT NOT NULL,
    bronze_path   TEXT NOT NULL,   -- the file that was re-read
    old_version   INTEGER NOT NULL,
    new_version   INTEGER NOT NULL,
    reason        TEXT NOT NULL,   -- what the parser got wrong, in plain words
    corrected_at  TIMESTAMP NOT NULL DEFAULT timezone('UTC', now())
);


-- ---------------------------------------------------------------------------
-- observation_log — the journal. The owner's own words, with a timestamp.
-- noted_at and note are never edited. Status only moves forward.
-- A rejected observation stays here forever: the misses are part of the record.
-- ---------------------------------------------------------------------------
-- DuckDB has no AUTOINCREMENT, so obs_id is fed by a sequence (a counter object).
CREATE SEQUENCE IF NOT EXISTS observation_log_id_seq START 1;

CREATE TABLE IF NOT EXISTS observation_log (
    obs_id        INTEGER PRIMARY KEY DEFAULT nextval('observation_log_id_seq'),
    noted_at      TIMESTAMP NOT NULL DEFAULT timezone('UTC', now()),  -- immutable, UTC
    note          TEXT NOT NULL,       -- free text, the owner's words
    series_ids    TEXT[],              -- which series were on screen
    window_start  DATE,                -- what date range was being looked at
    window_end    DATE,
    status        TEXT NOT NULL DEFAULT 'noted',  -- noted | testing | supported | rejected
    test_ref      TEXT,                -- path to the query/notebook that tested it
    resolved_at   TIMESTAMP
);


-- ---------------------------------------------------------------------------
-- split_mask — the holdout. 25% of ISO weeks, chosen once with a fixed seed.
-- Rows are loaded from db/split_mask.csv, which is committed to git and never
-- regenerated. See db/make_split.py.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS split_mask (
    iso_week      TEXT PRIMARY KEY,    -- '2026-W14'
    split         TEXT NOT NULL        -- 'explore' | 'holdout'
);


-- ---------------------------------------------------------------------------
-- Views
-- ---------------------------------------------------------------------------

-- observations_latest — our best current answer for each (series, period).
-- Two stages, and the order matters:
--   1. within one vintage, keep the highest parse_version — the latest reading
--      of that payload, i.e. the corrected one if a parser bug was fixed;
--   2. across vintages, keep the most recent received_at.
-- Doing it the other way round could pick a superseded parse of a newer vintage.
-- QUALIFY filters on a window function: keep row 1 after sorting each group.
CREATE OR REPLACE VIEW observations_latest AS
WITH best_parse AS (
    SELECT * FROM observations
    QUALIFY row_number() OVER (
        PARTITION BY feed_id, series_id, entity_id, period_start, received_at
        ORDER BY parse_version DESC
    ) = 1
)
SELECT * FROM best_parse
QUALIFY row_number() OVER (
    PARTITION BY feed_id, series_id, entity_id, period_start
    ORDER BY received_at DESC
) = 1;

-- observations_explore — what the owner is allowed to look at.
-- Holdout weeks are simply absent. Gaps in the charts are supposed to be gaps.
-- strftime(date, '%G-W%V') turns a date into its ISO week label, e.g. '2026-W14'.
CREATE OR REPLACE VIEW observations_explore AS
SELECT o.* FROM observations_latest o
JOIN split_mask m ON strftime(o.period_start, '%G-W%V') = m.iso_week
WHERE m.split = 'explore';

-- observations_holdout — used ONLY by hand, from queries/, when testing a
-- logged observation. The dashboard must never import this.
CREATE OR REPLACE VIEW observations_holdout AS
SELECT o.* FROM observations_latest o
JOIN split_mask m ON strftime(o.period_start, '%G-W%V') = m.iso_week
WHERE m.split = 'holdout';
