# Design — v0

Deliberately small. Every choice below optimises for being able to change it later
without losing data.

## Layers

```
  ┌───────────────────────────────────────────────┐
  │  app        Streamlit page · Kepler.gl map     │   cheapest, most replaceable
  ├───────────────────────────────────────────────┤
  │  silver     observations · entity_registry ·   │   the actual asset
  │             feed_registry   (DuckDB)           │
  ├───────────────────────────────────────────────┤
  │  bronze     raw payload files, append-only     │   the insurance policy
  ├───────────────────────────────────────────────┤
  │  ingestors  one plain function per feed        │
  └───────────────────────────────────────────────┘
```

Gold (features), models, and agents do not exist in v0.

## Bronze — raw payloads

Every HTTP response is written to disk **before** parsing:

```
data/bronze/<feed_id>/<received_at ISO, colons replaced>.json
```

Rules: never modified, never deleted, committed to `.gitignore` (not to git). If
parsing fails, the file still exists and can be reprocessed once the parser is
fixed. This is the cheapest insurance in the whole system.

## Silver — the `observations` table

One long, narrow table for every numeric series from every feed. "Long" means one
row per (series, period, vintage) rather than one column per series. It looks
wasteful and it is the correct shape for time-series data with revisions.

```sql
CREATE TABLE observations (
    feed_id        TEXT NOT NULL,   -- which ingestor produced this
    series_id      TEXT NOT NULL,   -- e.g. 'hormuz_transits', 'crude_stocks_kb', 'brent_usd'
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
```

**Why two time axes.** `period_start` is what the number is *about*. `received_at`
is when we *had* it. A value for the week of 3 March that we fetched on 10 March and
again (revised) on 17 March produces two rows. Querying "what did we know on 12
March" is a `WHERE received_at <= '2026-03-12'` filter plus taking the latest
vintage per period. Without this, every backtest silently uses data from the future.

**Why a third axis, `parse_version`.** `received_at` answers "when did the
source's number reach us". It cannot answer "and did we read it correctly". If a
parser is found to have been wrong — a decimal point, a unit, a mis-read field —
the fix is to re-read the same bronze file with the corrected parser, keep the
original `received_at`, and write the corrected rows as `parse_version = 2`. The
wrong rows stay for ever as evidence of what we believed at the time. Nothing is
updated and nothing is deleted, so the repair is itself append-only and
auditable.

The two rules that keep the axes from blurring into each other:

- a new `received_at` is **only** for a fresh fetch from the source;
- `parse_version` increments **only** when re-reading a bronze file we already
  hold.

Putting a corrected parse under a new `received_at` would misrepresent our own
bug as a revision by the source, which is exactly the confusion the bitemporal
design exists to prevent. See docs/QUESTIONS.md Q1, answered 2026-09-11.

**The "latest known" view**, which is what the dashboard reads. Two stages, in
this order: first keep the highest `parse_version` within a vintage, then keep
the most recent vintage. The other order would let a corrected old vintage
outrank an uncorrected newer one.

```sql
CREATE VIEW observations_latest AS
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
```

Point-in-time queries are the same view with a `received_at <= :asof` filter added.

## Silver — `parse_corrections`

Why a bronze file was ever read a second time. Append-only. Without it, a jump
from `parse_version` 1 to 2 in `observations` is a mystery in six months.

```sql
CREATE TABLE parse_corrections (
    correction_id INTEGER PRIMARY KEY,
    feed_id       TEXT NOT NULL,
    bronze_path   TEXT NOT NULL,   -- the file that was re-read
    old_version   INTEGER NOT NULL,
    new_version   INTEGER NOT NULL,
    reason        TEXT NOT NULL,   -- what the parser got wrong, in plain words
    corrected_at  TIMESTAMP NOT NULL
);
```

## Silver — `entity_registry`

```sql
CREATE TABLE entity_registry (
    entity_id     TEXT PRIMARY KEY,  -- canonical, never changes
    entity_type   TEXT NOT NULL,     -- 'chokepoint', 'country', 'benchmark', 'port', 'vessel', 'company'
    id_scheme     TEXT NOT NULL,     -- 'PORTWATCH', 'ISO3166A3', 'INTERNAL', 'UNLOCODE', 'IMO', 'LEI'
    display_name  TEXT NOT NULL,
    lat           DOUBLE,
    lon           DOUBLE,
    notes         TEXT
);

CREATE TABLE entity_alias (
    alias         TEXT NOT NULL,     -- any name or code a source uses
    scheme        TEXT NOT NULL,     -- where that alias comes from
    entity_id     TEXT NOT NULL REFERENCES entity_registry(entity_id),
    PRIMARY KEY (alias, scheme)
);
```

v0 seeds three rows. The point is that the table exists so that feed number four
maps into it instead of inventing its own naming.

## Silver — `ingest_runs`

```sql
CREATE TABLE ingest_runs (
    run_id        INTEGER PRIMARY KEY,
    feed_id       TEXT NOT NULL,
    received_at   TIMESTAMP NOT NULL,
    started_at    TIMESTAMP NOT NULL,
    finished_at   TIMESTAMP,
    status        TEXT NOT NULL,      -- 'running' | 'ok' | 'failed'
    rows_fetched  INTEGER,
    rows_inserted INTEGER,
    bronze_path   TEXT,
    error         TEXT                -- redacted, first 500 chars
);
```

Written at the start and end of every ingestor run. The first place to look
when something is wrong. See ARCHITECTURE.md §5.

## Silver — `feed_registry`

```sql
CREATE TABLE feed_registry (
    feed_id       TEXT PRIMARY KEY,
    provider      TEXT NOT NULL,
    upstream      TEXT NOT NULL,     -- plain text. Where does this REALLY come from.
    cadence       TEXT NOT NULL,     -- 'daily', 'weekly', 'monthly'
    endpoint      TEXT NOT NULL,
    license_notes TEXT,
    added_on      DATE NOT NULL
);
```

`upstream` is the one column here that is not obvious. It exists so that when two
feeds agree, you can check whether they are independent or two views of the same
underlying source. Free text is enough for now.

## Exploration support — from database to UI

v0 is an observation phase. The owner watches feeds and notices things. Two
objects make that honest.

### `observation_log` — the journal

```sql
CREATE TABLE observation_log (
    obs_id        INTEGER PRIMARY KEY,
    noted_at      TIMESTAMP NOT NULL DEFAULT now(),  -- when it was written. Immutable.
    note          TEXT NOT NULL,       -- free text, the owner's words
    series_ids    TEXT[],              -- which series were on screen
    window_start  DATE,               -- what date range was being looked at
    window_end    DATE,
    status        TEXT NOT NULL DEFAULT 'noted',  -- noted | testing | supported | rejected
    test_ref      TEXT,                -- path to the query/notebook that tested it
    resolved_at   TIMESTAMP
);
```

Rules: `noted_at` and `note` are never edited. Status moves forward only.
A rejected observation stays in the table forever — the misses are as much
of the record as the hits.

### `split_mask` — the holdout

```sql
CREATE TABLE split_mask (
    iso_week      TEXT PRIMARY KEY,    -- '2026-W14'
    split         TEXT NOT NULL        -- 'explore' | 'holdout'
);
```

Generated once by `db/make_split.py` with a fixed seed: 25% of ISO weeks
across the full date range, chosen at random, marked `holdout`. Committed to
git so it never changes. Blocking by whole weeks (rather than random days)
matters for time series — adjacent days are not independent, so day-level
holdout leaks.

### The views the app reads

```sql
-- what the owner looks at. Holdout weeks are simply absent.
CREATE VIEW observations_explore AS
SELECT o.* FROM observations_latest o
JOIN split_mask m ON strftime(o.period_start, '%G-W%V') = m.iso_week
WHERE m.split = 'explore';

-- used ONLY by hand, from queries/, when testing a logged observation.
CREATE VIEW observations_holdout AS
SELECT o.* FROM observations_latest o
JOIN split_mask m ON strftime(o.period_start, '%G-W%V') = m.iso_week
WHERE m.split = 'holdout';
```

The app imports `observations_explore` and nothing else. Gaps in the charts
are the holdout weeks. They are supposed to look like gaps.

### In the UI

Every chart page has a **"Note this"** box. Typing a sentence and pressing
enter writes a row to `observation_log` with the series currently on screen and
the visible date range attached automatically. A separate **Log** page lists
entries newest-first with their status. There is no edit button.

### The test path (v1, recorded here so the schema supports it)

An observation moves to `testing` when someone writes a query under
`queries/tests/<obs_id>.sql` that runs against `observations_holdout`. The
result — supported or rejected — is written back with `test_ref`. This is the
whole hypothesis lifecycle: notice, log, test on unseen data, record the answer.

## Ingestors

One file per feed: `ingest/portwatch.py`, `ingest/eia.py`, `ingest/fred.py`.
Each exposes one function `run(conn, received_at=None)` that:

1. Fetches the payload.
2. Writes it to bronze.
3. Parses it into rows matching `observations`.
4. Inserts with `INSERT ... ON CONFLICT DO NOTHING` (the primary key includes
   `received_at`, so re-running with the same timestamp is a no-op and re-running
   later appends a vintage).

No shared base class. If the three files look similar, that is fine.

## App

`app/dashboard.py` — Streamlit, reads `observations_explore` only, three line
charts, one "last received" table, a "Note this" box on every chart page, and a
Log page. `app/export_map.py` — writes `entity_registry` rows with coordinates to
CSV for Kepler.gl. Nothing else.

## Testing

`tests/test_idempotency.py` — for each ingestor: run against a fixture payload,
count rows; run again with a later `received_at`; assert count doubled and every
original row is byte-identical.

## What v1 will need that v0 does not build

Recorded so it is not forgotten, not so it is built now:

- A scheduler.
- A `features` table (gold) derived from `observations_latest`.
- Point-in-time joins across feeds at mixed frequencies.
- A `forecasts` table for the ledger.
- Entity coordinates for many more entities (ports, vessels).

None of these change the v0 schema. That is the test of whether v0 is right.

## v1 addition — the graph and its gaps (recorded now, built in v1)

The owner's target state is an exploration tool: pick a central entity, see its
ecosystem as a graph, click an edge to isolate the value chain, with a map
carrying the physical flows. The foundational object for that is an edge table.
The schema is fixed now so v0 does not need to change when v1 arrives.

```sql
CREATE TABLE edges (
    edge_id       INTEGER PRIMARY KEY,
    from_entity   TEXT NOT NULL REFERENCES entity_registry(entity_id),
    to_entity     TEXT NOT NULL REFERENCES entity_registry(entity_id),
    relation      TEXT NOT NULL,     -- 'supplies', 'refines_into', 'ships_via', 'buys_from'
    status        TEXT NOT NULL,     -- 'observed' | 'inferred' | 'gap'
    feed_id       TEXT,              -- which feed backs it, if status = observed
    confidence    TEXT,              -- free text for now: 'strong', 'weak', 'guess'
    source        TEXT,              -- citation or reasoning, always filled
    gap_reason    TEXT,              -- if status = gap: why nobody has this
    gap_status    TEXT,              -- 'open' | 'researching' | 'proxy_found' | 'needs_human_intel'
    added_on      DATE NOT NULL,
    updated_on    DATE NOT NULL
);
```

Rules:
- Every edge has a `source`, even a guess. "I think so" is a source; blank is not.
- `status = 'gap'` is a first-class state, not an absence. Gaps are rendered in
  the UI, visibly (red), never hidden.
- A new gap edge automatically becomes an entry in `docs/QUESTIONS.md` for the
  research session. Research returns one of: a direct feed, a proxy that lets
  the edge become `inferred`, or nothing — in which case `gap_status` becomes
  `needs_human_intel` and the edge stays red with the reason attached.
- Physical commodity legs (field → port → tanker → port) can be `observed` via
  AIS and customs feeds. Downstream legs (petrochemicals → wafer chemicals →
  fabs → chips → labs) are expected to be mostly `inferred` or `gap`. The UI
  must make that difference obvious, not smooth it over.
- Render in 2D first (force-directed graph, click to isolate a chain). 3D is a
  rendering decision for later, taken only when 2D is visibly insufficient.
- Start with oil and gas, three or four hops, hand-curated. Extend toward
  semiconductors only after the oil-and-gas graph has real observed edges.
