# Decisions

Append-only. Newest at the bottom. Each entry: date, decision, why, what it rules out.
Reversals are new entries that reference the old one, not edits.

---

**2026-09-04 — One vertical first: energy + shipping.**
Why: richest free data, and the owner already has domain context from the Hormuz
work. Rules out: parallel builds for semis and agriculture. Those become
configuration once the spine works.

**2026-09-04 — Append-only bitemporal storage from day one.**
Why: revised data overwrites itself in every free feed; without a `received_at`
vintage you cannot reconstruct what was known when, and every backtest is
contaminated by future information. Cost now is one column and one rule. Cost to
retrofit is total. Rules out: any UPDATE or DELETE on `observations`.

**2026-09-04 — Plain-text `upstream` on every feed.**
Why: multiple feeds often derive from one underlying source (e.g. several AIS
providers). Agreement between them is not independent confirmation. A free-text
field is enough to know this; a formal provenance graph is parked.

**2026-09-04 — Canonical IDs for entities; names are aliases.**
Why: ship names, port names and company names change and collide. IMO, UN/LOCODE,
LEI, ISO 3166 do not. Rules out: joining on names anywhere.

**2026-09-04 — DuckDB single file, not Postgres.**
Why: zero setup, fast analytics on a laptop, native Parquet. Migrate to Postgres or
Timescale only when concurrent writes or a scheduler demand it. Rules out: any
ORM.

**2026-09-04 — No abstraction across ingestors in v0.**
Why: three feeds is not enough to know what the right abstraction is. Premature
frameworks are the most common way these projects die. Rules out: base classes,
registries, plugin loaders until v1.

**2026-09-04 — Owner hand-writes the first ingestor.**
Why: the stated goal is to learn the space, not to own a system that cannot be
debugged. The second and third ingestors can be delegated.

**2026-09-04 — All theory-derived features parked until after v1.**
Why: the infonomics framework (see PARKING_LOT.md) suggests several genuinely
useful capabilities, but building them before real data flows is scope creep with
a sophisticated justification. Revisit at the v1 retro with actual data in hand.

**2026-09-04 — No execution layer, ever, in this plan.**
Why: owner's decision, and the advisor agrees. Retail loss statistics on
automated/leveraged trading are conclusive. The system informs slow decisions; it
does not place orders.

**2026-09-04 — v0 is an observation phase, not a hypothesis-testing phase.**
Why: the owner cannot state a hypothesis about a domain they have not yet
watched, and demanding one would produce a fake one. Exploration is legitimate
science. Rules out: any v0 task that requires a stated claim.

**2026-09-04 — Observation log with immutable, timestamped entries.**
Why: eyes find patterns in noise and memory keeps the hits and drops the misses.
Writing a dated note before checking turns a feeling into a testable candidate
and preserves the misses. Rules out: any edit or delete on `observation_log`.

**2026-09-04 — Week-blocked holdout, 25%, fixed seed, hidden from the UI.**
Why: a pattern found by looking at data can only be tested honestly on data
that was not looked at. Blocking by ISO week rather than random days because
adjacent days in a time series are not independent and day-level holdout leaks.
Fixed seed and committed CSV so the split cannot drift. No "show all" toggle
because the moment it exists it gets used. Rules out: the app ever reading
`observations_latest` or `observations_holdout` directly.

**2026-09-04 — Feed endpoints verified before week 1, not during week 2.**
Why: PortWatch is an ArcGIS layer, not a plain REST API. Discovering an awkward
response shape mid-build costs a week; discovering it in a research session
costs an hour.

**2026-09-04 — Dependencies are exactly the six named in PLAN.md.**
Why: `duckdb pandas httpx streamlit pytest python-dotenv` and nothing else.
Transitive dependencies (pyarrow, numpy, altair and so on) come in via those and
are pinned in `uv.lock`. Rules out: adding a library without a new entry here.

**2026-09-04 — `obs_id` comes from a DuckDB sequence, not AUTOINCREMENT.**
Why: DESIGN.md specifies `obs_id INTEGER PRIMARY KEY` but DuckDB has no
AUTOINCREMENT keyword, so `observation_log_id_seq` supplies the value via
`DEFAULT nextval(...)`. Same behaviour, one extra object in `schema.sql`.
The boring option; the alternative was making the app compute the next id, which
would race the moment anything else writes.

**2026-09-04 — `noted_at` defaults to `current_localtimestamp()`, not `now()`.**
Why: DuckDB's `now()` returns a timestamp *with* a time zone, and the column is a
plain `TIMESTAMP`. `current_localtimestamp()` returns local wall-clock time and
needs no cast. Consequence: everything in this database is naive local time.
Fine for a single-machine, single-owner v0; revisit if the system ever runs
somewhere other than the owner's laptop.

**2026-09-04 — Holdout split: seed 20260904, ISO weeks 2015-W01 to 2030-W52.**
Why: 835 weeks, 209 (25.0%) marked holdout, written once to `db/split_mask.csv`
and committed. `db/make_split.py` refuses to overwrite an existing CSV and errors
loudly if regeneration would produce something different, so the split cannot
drift silently. The CSV is the source of truth; the `split_mask` table is a copy
of it loaded by `db/init.py`.

**2026-09-04 — `db/init.py` is idempotent and loads the split mask itself.**
Why: `CREATE TABLE IF NOT EXISTS`, `CREATE OR REPLACE VIEW` and `INSERT OR IGNORE`
throughout, so running it again re-asserts the schema without touching ingested
rows. It loads `split_mask.csv` because `observations_explore` is empty and
silently wrong without it — a database that builds but hides everything is worse
than one that will not build. Rules out: a separate load step to forget.

**2026-09-04 — `feed_registry` is not seeded; each ingestor inserts its own row.**
Why: rule 2 says every feed declares its upstream, and the reliable way to keep
that true is for the code that fetches a feed to be the code that registers it —
a seed file would drift from the ingestors the first time an endpoint changes.
Consequence: each `ingest/*.py` `run()` starts with an `INSERT OR IGNORE INTO
feed_registry`, using the provider/upstream/cadence/endpoint already written down
in `docs/feeds/<feed>.md`. `feed_registry` is therefore empty until the first
ingestor runs, which is correct: no feed has run yet.
