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
    PRIMARY KEY (feed_id, series_id, entity_id, period_start, received_at)
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
    noted_at      TIMESTAMP NOT NULL DEFAULT current_localtimestamp(),  -- immutable
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

-- observations_latest — the most recent vintage of each (series, period).
-- QUALIFY filters on a window function: keep row 1 after sorting each
-- (feed, series, entity, period) group by received_at descending.
CREATE OR REPLACE VIEW observations_latest AS
SELECT * FROM observations
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
