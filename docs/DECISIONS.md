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

**2026-09-04 — Keys may come from the shell environment as well as `.env`.**
Why: `.env` is a file of environment variables, so a cloud session that sets
`EIA_API_KEY` and `FRED_API_KEY` in its own environment settings is the same
mechanism by a different route, not a second configuration system. Code reads
`os.environ` and does not care which filled it. This matters because pasting a
key into a chat window to get it into a container is worse than setting it once
in the environment. Rules out: any config file, config class or settings module
beyond `.env`. Amends the README line that said `.env` only.

**2026-09-04 — `received_at` is our clock; `source_asof` is the source's.**
Why: a check of the FRED keys found that `realtime_start` is the date that
series was last refreshed, not today — Brent returned 2026-09-02 while OVX
returned 2026-09-04 in calls seconds apart. The tempting conclusion is that an
ingestor should stamp `received_at` with the returned `realtime_start` rather
than "substitute" its own clock. That is wrong and would break rule 1's
mechanism: `received_at` is in the primary key, so a series FRED has not
refreshed for a week would produce an identical key on every run, `INSERT OR
IGNORE` would drop the rows, and the Week 2 idempotency test (run twice, row
count doubles) would fail. `realtime_start` belongs in `source_asof`, which
DESIGN.md defines as "when the SOURCE says it published, if known". Rules out:
any ingestor deriving `received_at` from anything but its own clock at fetch
time. Recorded in `docs/feeds/fred.md` as a table, since this is the first
place the two time axes could plausibly be confused.

**2026-09-05 — CC writes `ingest/fred.py`; the owner does not hand-write it.**
Why: owner's explicit call, reversing the 2026-09-04 entry "Owner hand-writes the
first ingestor". That entry's reason was that the owner should not own a system
they cannot debug. The reason still stands, so it is met a different way: CC
writes the file and walks the owner through it line by line, and the Week 4 gate
— explain every table and column out loud without looking — is unchanged and
still the real test. If that gate is failed, this decision was wrong and should
be revisited rather than the gate lowered.

**2026-09-05 — Ingestors pull from 2015-01-01, not from the start of history.**
Why: `split_mask` only covers ISO weeks 2015 to 2030, and `observations_explore`
inner-joins it, so a row dated before 2015-W01 has no split assignment and would
silently vanish from every view — present in the table, invisible in the app,
which is the worst of both. DCOILBRENTEU goes back to 1987; that history is not
useful until the split is extended, which it never will be, because the CSV is
committed and fixed. Rules out: full-history pulls without first extending
`split_mask`. Overridable per call via `observation_start` if a query ever needs
the older data by hand.

**2026-09-05 — Bronze stores the response body verbatim, inside an envelope.**
Why: the first version re-serialised FRED's JSON, which preserved the content but
not the bytes. Bronze is supposed to be evidence, and evidence you have
reformatted is weaker evidence. Each file is now
`{envelope_version, feed_id, received_at, endpoint, request, responses}` where
each response holds the exact text off the wire plus its status code. The
envelope adds provenance — when we asked, what we asked for — so a file is
readable on its own in two years. The API key is deliberately not recorded:
a secret in a data file is a secret you forget you wrote down. Rules out:
parsing, filtering or reformatting anything on the way into bronze.

**2026-09-05 — Bronze has a read path, not just a write path.**
Why: the stated justification for bronze was "if the parser is wrong, re-read
the file instead of re-fetching", and nothing implemented that — the insurance
could not be claimed. `read_bronze()` and `run_from_bronze()` now exist, wired to
`--reparse`. Verified by deleting the database and rebuilding 12,180 rows across
two vintages from bronze alone, with `FRED_API_KEY` unset. Re-parsed rows keep
the file's original `received_at`, because that is genuinely when the data
arrived; inventing a fresh one would claim a vintage that never happened. The
open question of how to repair a vintage stored *wrongly* is Q1 in
docs/QUESTIONS.md and is deliberately not answered here.

**2026-09-05 — Validation checks shape, never plausibility.**
Why: a reply is refused if a series is missing, empty, has a repeated date, has a
date outside the window we asked for, or has a value that is neither a number
nor FRED's `"."`. It is not refused for being surprising. A rule like "an oil
price must be positive" would have rejected April 2020, when WTI genuinely
settled below zero — the single most informative day in the modern history of
the series. There is a test asserting a negative price is accepted. Rules out:
range checks, outlier rejection, and smoothing anywhere in the ingest path.

**2026-09-05 — Tests brought forward from week 2, and run offline.**
Why: until now the only thing verifying rule 1 was a person running the ingestor
twice and reading the counts. `tests/test_idempotency.py` has 16 tests against a
saved payload in `tests/fixtures/`, so they need no API key, no network and no
`data/` directory, and give the same answer on any machine. They found a real
bug on first run: `parse()` raised on any bronze file outside the repo, which
`--reparse` accepts by design. Rules out: tests that call a live API.
