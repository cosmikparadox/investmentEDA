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

**2026-09-11 — Gaps are first-class objects, rendered red, never hidden.**
Why: the value-chain graph will be mostly hand-curated and partly guesswork.
Rendering only what is known makes beliefs look like facts. Rendering gaps
explicitly turns the weakness into the product: a map of the owner's actual
information position. Every gap becomes a research ticket. Rules out: any UI
that omits edges because they are unknown.

**2026-09-11 — Edge table added to the v1 schema now; graph UI built in v1.**
Why: the target state (entity → ecosystem graph → isolated value chain → map of
physical flows) needs an edge table as its foundation. Fixing the schema now
means v0 does not change. 2D force graph before 3D. Rules out: 3D rendering
until 2D is shown to be insufficient.

**2026-09-11 — "Real-time" applies to the physical commodity leg only.**
Why: crude on tankers is trackable live (aisstream, free). Nothing downstream
of the refinery has a public live feed. The UI must distinguish live-observed
edges from slow-curated ones. Rules out: presenting the downstream chain as live.

**2026-09-11 — Polling on a timer is the near-real-time compromise.**
Why: FRED, CME delayed and GDELT change every 10 min to daily; a scheduled pull
every 10–15 min is indistinguishable from streaming for a slow decision and
needs no new infrastructure. One isolated live websocket (aisstream) is the only
true stream in v1. Rules out: Kafka, Flink, or any message queue until there are
multiple producers and consumers.

**2026-09-11 — Charter, PRD and architecture documents added.**
Why: the target state is now well enough understood to write down, and the
build agent needs the destination and the engineering standard to avoid
painting into corners. These documents describe direction and quality bar;
they do not expand v0 scope. Rules out: any [v1]+ requirement being built
in v0 on the grounds that "the PRD mentions it".

**2026-09-11 — `ingest_runs` table added to v0.**
Why: observability is cheap now and essential the first time a feed silently
stops. One table, written at run start and end. Rules out: ingestors that
succeed or fail without a record.

**2026-09-11 — `core/` package with typed errors, redacting logger, single
HTTP helper.**
Why: the one place tests patch, the one place keys get redacted, the one place
timeouts are set. Small enough not to count as a framework. Rules out: raw
`httpx` calls inside ingestors.

**2026-09-11 — The 11 September document set was merged into the repo, not
copied over it.**
Why: the research session's documents were written from the 4 September state of
the repo, so several of them are older than what is here — `docs/QUESTIONS.md`
(Q1), `docs/feeds/fred.md` and `docs/feeds/eia.md` (live-call findings) and
`README.md` (setup steps, keys from the environment) all carry build-session work
that the incoming copies do not. Overwriting would have deleted findings that
cost a live API call to learn. So: CHARTER, PRD and ARCHITECTURE are new files
taken as given; CLAUDE.md, DESIGN.md, SCOPE.md and PARKING_LOT.md are taken whole
because only the research session had changed them; PLAN.md and DECISIONS.md are
merged — the newly added Week 1 tasks and the seven entries above sit alongside
the ticks and entries already here; QUESTIONS.md, README.md and the two feed
specs are kept as they were. `FIRST_PROMPT_FOR_CLAUDE_CODE.md` is not added: it
is the bootstrap prompt and says to delete it once setup is done. Rules out:
treating a document drop as a wholesale replacement of the repo's memory.

**2026-09-11 — `core/` and `ingest/runs.py` built now; the owner migrates
`ingest/fred.py` onto them.**
Why: the owner's answer to Q2, recorded there in full. The short version: the
three-cases rule is about the shape of an ingestor, not about config loading,
logging, HTTP timeouts and error types, which any project has whether it holds
one feed or fifty. Shared functions yes, shared shape no — CLAUDE.md's first
forbidden bullet was amended to say exactly that. Rules out: a second ingestor
written against raw `httpx` and its own exception type.

**2026-09-11 — A missing API key is reported when a feed needs it, not when
`core.config` is imported.**
Why: ARCHITECTURE.md §6 says missing keys raise at import time. Taken literally
that breaks the things that are supposed to work without keys — `db/init.py`,
the dashboard, and every test — because importing anything that imports config
would fail on a machine with no `.env`. So `.env` is still read once at import,
but the raise happens in `api_key("FRED_API_KEY")`, at the moment a feed
actually reaches for it, and the message names the key and the URL to register
for one. Rules out: a config module that cannot be imported without secrets.

**2026-09-11 — `core.http` exposes `get()` returning text as well as
`get_json()`.**
Why: ARCHITECTURE.md §3.1 specifies `get_json`, but bronze stores the response
body verbatim (2026-09-05), and a function that parses JSON and throws the text
away cannot serve that. `get()` returns status, text and a key-redacted URL;
`get_json()` is `get()` plus `json.loads`. Both set the same timeouts and raise
the same `FeedError`. Rules out: an ingestor re-serialising JSON on its way into
a bronze file to work around the helper.

**2026-09-11 — A fourth error class, `ConfigError`.**
Why: ARCHITECTURE.md §4 names three. A missing key is not a feed failure, a
parse failure or a storage failure — it is the system being unconfigured, and
before any feed is involved. It is a `ControlroomError` like the rest, so
anything catching that catches this too. Rules out: `SystemExit` raised from
library code, which is what `ingest/fred.py` does today and which cannot be
caught by a caller that wants to record the failure.

**2026-09-11 — `ingest_runs` rows are updated once, by the run that wrote them.**
Why: ARCHITECTURE.md §5 says the row is written at start and end, which means
the end has to fill in the row the start created. That is an UPDATE, and rule 1
says no UPDATEs — but rule 1 is about never overwriting what a source told us.
`ingest_runs` is a logbook of our own attempts, not data from a source. The
UPDATE is narrow by construction: it only matches a row still marked 'running',
so finishing a run twice is an error rather than a silent rewrite, and a process
killed mid-run leaves its row saying 'running' for ever, which is the signal you
want. Rules out: a second `ingest_runs` row per run, which would make "how many
times did this feed run" a question about de-duplication.

**2026-09-11 — `Settings.__repr__` prints "set"/"missing", never a key.**
Why: writing this module, `print(settings)` put both live API keys on screen,
because that is what Python does with a dataclass. The redaction filter did not
help: it covers log lines, and that was a print. A secret that can be leaked by
the most obvious debugging command in the language will be. Rules out: any
object holding a key whose default repr shows it.

**2026-09-11 — `parse_version` added to `observations` and to its primary key.**
Why: the owner's answer to Q1, recorded there in full. A vintage stored wrongly
could not be corrected without breaking rule 1; now it is corrected by re-reading
the same bronze file under the same `received_at` with the next `parse_version`,
so the wrong rows stay as evidence and the repair is itself append-only. The two
axes stay honest: a new `received_at` means the source said something new, a new
`parse_version` means we read the same thing better. Rejected on the way:
`superseded_by` (needs an UPDATE), delete-and-reinsert (destroys the evidence),
and a fresh `received_at` (dresses our bug up as the source's revision).
Rules out: any correction path that changes or removes a stored row.

**2026-09-11 — `observations_latest` is two-stage, parse first, vintage second.**
Why: highest `parse_version` within a vintage, then most recent vintage. The
other order lets a corrected old vintage outrank an uncorrected newer one, which
would show the owner a number the source has already superseded. There is a test
for exactly this. Rules out: a single QUALIFY over both columns at once.

**2026-09-11 — `db/migrations.py`, and `db/init.py` migrates before it creates.**
Why: `CREATE TABLE IF NOT EXISTS` silently leaves an old table alone, so without
a migration an existing database would keep the old primary key while the new
views expect the new column, and the failure would surface somewhere confusing.
A primary key cannot be altered in place, so the migration renames the table,
lets `schema.sql` build the new one, copies every row across as
`parse_version = 1` — true of everything written before today — checks the count
matches, and only then drops the old table, all in one transaction. Deleting
`data/` instead was rejected: bronze can rebuild `observations`, but nothing can
rebuild the owner's hand-written `observation_log` notes. Rules out: schema
changes that assume a fresh database.

**2026-09-11 — Every TIMESTAMP in the database is UTC, stored naive, from
`core.clock.utc_now()`.**
Why: the owner's answer to Q3, which reverses the 2026-09-04 decision to use
`current_localtimestamp()` and local `datetime.now()`. That entry's reasoning
was "fine for a single-machine, single-owner v0, revisit if it ever runs
somewhere else" — and it already does, since this repo is worked on from a cloud
session whose clock is UTC while the owner's laptop is on London time. Two
machines writing `received_at` in two zones, into a primary key, would make "what
did we know on 5 September" unanswerable. Naive rather than DuckDB's aware type
because mixing the two makes every comparison a question about which is which;
one convention applied everywhere is easier to keep true, and it is written at
the top of `schema.sql` where anyone writing a query will meet it. Rules out:
`datetime.now()`, `current_localtimestamp()`, and any timestamp not obtained
from `core.clock`.

**2026-09-11 — The UTC cutover, recorded so the old rows can be corrected later
if anyone cares.**
Per the Q3 answer, rows written before this change were left as they are. What
is known about them, exactly:

- **`observations`** — every row whose `received_at` predates the first run of
  the migrated `ingest/fred.py` was stamped with the machine's local clock. That
  machine was on British Summer Time, UTC+1, for all of them (BST ran from
  2026-03-29 to 2026-10-25, and the rows date from 4–5 September). To compare
  one of those timestamps with a UTC one, subtract one hour. The same applies to
  the `received_at` in their bronze filenames, which were written from the same
  value.
- **`ingest_runs`** — UTC from `run_id` 1 onwards. The table was created today
  and nothing had written to it before `ingest/runs.py` moved onto
  `core.clock`, so there is no mixed history to disentangle.
- **The exact cutover** — the first run of the migrated ingestor is the boundary,
  and it has not happened yet, because migrating `ingest/fred.py` is the owner's
  task under Q2. When it does: record its `run_id` and `started_at` here, in an
  entry underneath this one. PLAN.md carries that as a line so it is not
  forgotten. Until then the boundary is simply "everything currently in
  `observations` is BST".

No attempt was made to rewrite the old rows: `received_at` is in the primary key
and in every bronze filename, so correcting a one-hour offset on daily and weekly
data would mean a second migration touching files on disk. The offset is
recorded instead, which costs nothing and loses nothing.

**2026-09-11 — `core/clock.py`, a module ARCHITECTURE.md §2 does not list.**
Why: the Q3 answer names `core.clock.utc_now()` as the single source of the
current time, so that every timestamp has one origin and tests can freeze it in
one place. It is four lines of code and it belongs beside the other shared
plumbing. ARCHITECTURE.md's module list is from 11 September and predates the
answer; this is an addition to it, not a departure from it. Rules out: a call to
`datetime.now()` anywhere outside this module.

**2026-09-11 — `ingest/bronze.py` written by CC; the owner migrates onto it.**
Why: the owner's answer to Q4. It takes bytes rather than text or a dict, because
anything else has already been interpreted — bronze is supposed to be what the
source actually sent. It writes to a temporary file in the same folder and
renames it into place, so a crash leaves either no file or a complete one, never
a truncated file that later looks like evidence. It refuses to overwrite an
existing path, which is rule 1 at its most literal. Rules out: an ingestor
writing a bronze file with `path.write_bytes()`, which can be interrupted
halfway and can silently replace a file already there.

**2026-09-12 — `.env` beats a variable already set in the environment.**
Why: reverses the 2026-09-04 entry, which had it the other way round. After the
FRED key was rotated, `.env` held the new key and this session's environment
still held the old one — and the old one won, so the code would have sent a dead
key and got a 401 that said nothing about why. Editing `.env` is the obvious
thing to do when a key changes, so it should be the thing that takes effect.
`load_dotenv(..., override=True)` in `core/config.py` and in `ingest/fred.py`.
Rules out: silently preferring a stale value because it was set first.

**2026-09-12 — The redaction filter formats a log record before redacting it.**
Why: it was only redacting `record.msg`, and a library that logs `"GET %s"` with
the URL as an argument keeps the key in `record.args`, untouched. httpx does
exactly that, and printed a live API key in full the first time a real request
went through the configured logger. `getMessage()` applies the arguments first;
the result is redacted and the args cleared. There is a test with a key passed
as a log argument. Rules out: a redaction filter that only covers the cases
where the whole message was built before logging.

**2026-09-12 — The UTC cutover happened: `run_id` 1, `started_at`
2026-09-12 10:03:44 UTC.**
Why: filling in the placeholder left in the 2026-09-11 cutover entry. The first
run of the migrated `ingest/fred.py` is the boundary between local-time and UTC
`received_at` values. Precisely:

- Anything in `observations` with `received_at` **before 2026-09-12 10:03:44**
  was written by the pre-migration code using the machine's local clock, which
  was British Summer Time. Subtract one hour to compare it with anything newer.
  The same applies to the timestamps in those rows' bronze filenames.
- Anything from that moment onward is UTC, from `core.clock.utc_now()`.
- `ingest_runs` is UTC for its whole life: `run_id` 1 is the run named above.

On the owner's laptop the rows from 4–5 September are the BST ones, and its own
`ingest_runs` starts at `run_id` 1 with the first run after pulling this commit —
the timestamp above is from the machine this ran on, not from that database. The
boundary rule is what matters and it is the same on both: BST before the first
recorded run, UTC after it.

**2026-09-12 — `ingest/fred.py` migrated by CC, not by the owner.**
Why: the owner delegated it, reversing the Q2 answer's split. Q2's reasoning for
the owner doing it was learning by using the plumbing; the Week 4 gate — explain
every table and column out loud without looking — is unchanged and is still the
real test of that. What the migration changed, beyond the swaps: `run()` now
returns a `RunResult` rather than a row count, and never raises for a feed
failure — a source that is down, refuses us, or sends nonsense is recorded in
`ingest_runs` and returned as failed, per ARCHITECTURE.md §3.1. Rules out: a
caller having to wrap `run()` in a try block to find out whether a feed worked.

**2026-09-12 — Re-reading an already-loaded bronze file requires a stated reason.**
Why: `run(conn, bronze_path=...)` with no `reason` raises `ValueError` when the
file's rows are already stored, because that case is a parser correction and
`parse_corrections.reason` is what makes the jump from version 1 to 2
explainable later. Re-reading a file that was never loaded — rebuilding a
database from bronze — is a plain first read and needs no reason. Rules out: a
silent correction, which is the thing Q1 was asked to prevent.

**2026-09-12 — `ingest/eia.py` and `ingest/portwatch.py` written as two more
plain modules, deliberately repetitive.**
Why: each is the same seven steps as `ingest/fred.py` — open the run, fetch,
bronze, validate, parse, insert, close the run — with its own `fetch`,
`validate` and `parse`. The repetition is the point at this stage: CLAUDE.md
allows shared functions and forbids a shared shape, and three concrete feeds now
exist to compare if an abstraction is ever proposed. What is shared is what is
genuinely identical (`core/`, `bronze`, `runs`); what differs is what each
source actually does, and that differs a lot. Rules out: a base ingestor class,
for now, on the grounds that the three files look similar.

**2026-09-12 — `period_start = period_end` for both new feeds, for different
reasons.**
Why: EIA crude stocks is a *stock* — the level of oil in tanks on that Friday —
so giving it a seven-day span would claim it describes the whole week, which it
does not. PortWatch transits are a *flow*, but over exactly one day, so the span
is that day. The distinction matters the first time someone averages them
together; it is written into both parsers as a comment rather than left to be
rediscovered. Rules out: inferring a period's length from a feed's publication
cadence, which would be wrong for both.

**2026-09-12 — `source_asof` is NULL for both new feeds.**
Why: FRED tells us when it last refreshed a series, so `ingest/fred.py` records
it. The EIA publishes on a schedule but puts no timestamp in the reply, and
PortWatch backfills silently with no indication of when a row was recomputed. A
schedule is not a timestamp. NULL says "the source did not tell us", which is
true; filling it with the release time would be inventing evidence. Rules out:
deriving `source_asof` from a cadence.

**2026-09-12 — PortWatch's `date` field is read in both shapes it might arrive in.**
Why: `docs/feeds/portwatch.md` recorded epoch milliseconds; the live endpoint
returns `"YYYY-MM-DD"` strings. ArcGIS serves `esriFieldTypeDateOnly` either way
depending on a server-side setting nobody here controls, and a flip would
otherwise corrupt or reject every period in the table. `to_date()` accepts a
string or a number and refuses anything else, with a test asserting both shapes
produce identical rows. The feed doc has been corrected. Rules out: trusting a
written field spec over what the endpoint actually returns.

**2026-09-12 — Two structural checks that look like content checks, and why they
are not.**
Why: `ingest/eia.py` refuses a reply whose `units` is not `MBBL`, and refuses
one where fewer rows arrived than `response.total` says exist. Neither judges
whether a number is plausible — the first catches the source redefining what
every stored number means, the second catches paging stopping early, which would
look exactly like a series that ends. The plausibility line is held elsewhere:
there are tests asserting that a 20-million-barrel weekly build and a collapse
of Hormuz traffic to zero are both stored without complaint. Rules out: range
checks, outlier rejection and smoothing, in these ingestors as in FRED's.

**2026-09-12 — PortWatch is registered with cadence 'weekly' though its rows are
daily.**
Why: `feed_registry.cadence` is how often the feed is *published*, which is what
the dashboard's staleness panel needs (ARCHITECTURE.md §5: warn if the newest run
is older than 2× the cadence). PortWatch publishes weekly, on Tuesdays, and each
release contains daily rows. The row granularity is already in the data, in
`period_start`. Rules out: reading `cadence` as the spacing between observations.

**2026-09-14 — `ruff` added as a development dependency.**
Why: ARCHITECTURE.md §7 and NFR-53 put `ruff` in `make check`, and it is the
only dependency added since the original six. It is a development tool, not
something the system imports, so it lives in the dev group and nothing shipped
depends on it. Configured with line-length 95 and the rule sets E, W, F, I, UP,
B — deliberately not the whole catalogue, because a linter that shouts about
style gets switched off, and then it is not catching the real errors either.
Fixing the existing code to pass it was 30 findings, all formatting or import
order, none of them bugs. Rules out: adding a formatter as well, for now; `ruff
check` is doing the work and `ruff format` would rewrite every file at once.

**2026-09-14 — `make ingest` is a Python module, not a Makefile loop.**
Why: FR-07 wants every feed to run even when one fails, and a non-zero exit at
the end if any did. A Makefile can do one or the other, not both. `ingest/
__main__.py` calls each feed's `run()`, collects the `RunResult`s, prints a
table and exits 1 if any failed. The feed list in it is written out by hand:
adding a feed means one more line, and there is no discovery, no registry and no
plugin mechanism — which is the thing CLAUDE.md actually forbids. Rules out:
`make ingest` silently reporting success because the last feed happened to work.

**2026-09-14 — The app reads through a read-only connection, and one small
query module.**
Why: FR-44 is enforced by a test that greps `app/` for the two view names it may
not touch, so those names must not appear there at all — not even in a comment
saying "never read this", which is one uncommented character away from doing it.
All the app's SQL lives in `app/queries.py` so the whole surface can be checked
by eye in one file. The connection is opened `read_only=True`: a dashboard has
no business writing to `observations`, and saying so in code means a mistake
cannot. The single exception is a note, which opens its own writable connection,
inserts one row and closes. Rules out: ad-hoc SQL in a page, and any code path
from the app to a table it should not touch.

**2026-09-14 — Holdout weeks are drawn as breaks by inserting an empty point,
and the app is not told which weeks they are.**
Why: UI-01 wants the gaps visible rather than interpolated. A chart joins the
last point before a hidden week straight to the first point after it, drawing a
clean line across the gap — the exact illusion the holdout exists to prevent. So
`break_the_line_at_missing_weeks()` puts a null into any ISO week with no rows
at all, which stops the line. It works out which weeks those are from the data
the app can already see, and never reads `split_mask`: the app does not need to
know *why* a week is absent, only that it is, and not reading the mask keeps the
app on the views ARCHITECTURE.md §3.5 allows it. Whole weeks only — breaking the
line at every weekend would make the charts unreadable and hide the real gaps.
Rules out: filling, smoothing or interpolating anything on the way to a chart.

**2026-09-14 — Three charts, one per feed, with a series switch on two of them.**
Why: PLAN.md says three charts and there are five series. One chart per feed,
with a small radio for the feeds that carry two series, shows all five without
inventing a fourth panel. Charts are never combined: Brent in dollars a barrel
and OVX as an index share an entity but not a scale, and putting them on one
axis would invite a comparison that means nothing. Rules out: a combined chart,
and a series nobody can reach.
