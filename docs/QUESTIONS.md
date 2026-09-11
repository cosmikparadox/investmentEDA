# Questions

Claude Code writes questions here instead of guessing. The research/coordination
session answers them and marks them resolved. Keep the resolved ones; they are
part of the record.

## Open

**Q3 (2026-09-11, CC) — UTC or local time? The PRD and the database disagree.**

PRD NFR-12 says "all timestamps UTC; no naive datetimes in the database". The
database does the opposite: the 2026-09-04 decision put `current_localtimestamp()`
on `observation_log.noted_at` and `ingest/fred.py` stamps `received_at` with
`datetime.now()`, both naive local time. `ingest/runs.py` has just been written
to match the database rather than the PRD, on the grounds that two tables
disagreeing about what a timestamp means is worse than either choice on its own,
and that a comparison between `ingest_runs.received_at` and
`observations.received_at` has to be meaningful.

This is cheap to fix now and expensive later: every stored vintage is a
timestamp, and mixing zones silently shifts "what did we know on 5 September" by
up to a day. Three options: leave it and amend NFR-12 to say local; switch new
code to UTC and accept two conventions in one database; or switch everything to
UTC and re-parse the existing bronze files under UTC `received_at` values, which
Q1's `parse_version` mechanism now makes possible without losing anything.

CC's lean is the third, but it is a change to what every existing row means, so
it is the owner's call. Not urgent while the machine stays in one time zone;
urgent the first time it does not, or the first time the clocks change.

**Q4 (2026-09-11, CC) — Is `ingest/bronze.py` still wanted, and who writes it?**

The Q2 answer commissioned "`core/` and `ingest/runs.py`" by name, and its
reasoning calls `ingest/bronze.py` borderline but justified; the CLAUDE.md
amendment lists it as required plumbing. It has not been written, because
`ingest/fred.py` already has a working `write_bronze()`/`read_bronze()` pair and
extracting them is part of moving that file — which is the owner's job under the
same answer.

Suggestion: the owner lifts those two functions out of `fred.py` into
`ingest/bronze.py` as part of the migration, adding the two things the
ARCHITECTURE.md §3.3 contract asks for that the current code does not do — write
to a temp file and rename (so a crash cannot leave half a file), and raise
`StorageError` rather than overwrite if the path already exists. CC reviews.
Alternative: CC writes it first so the owner has it to migrate onto.

## Resolved

**Q1 (2026-09-05, CC) — How do we repair a vintage that was stored wrongly?**

Bronze now has a working read path: `ingest/fred.py --reparse FILE` re-reads a
saved payload and can rebuild the whole database from disk with no network and
no API key. Verified by wiping `data/controlroom.duckdb` and restoring 12,180
rows across two vintages from the bronze files alone.

But it only *adds*. If a parser bug wrote wrong values under a `received_at`,
re-parsing after the fix adds nothing, because those primary keys already exist
and `INSERT OR IGNORE` skips them. Correcting them means deleting rows, and rule
1 forbids UPDATE and DELETE on `observations`.

Three options, none obviously right:

1. **Never repair.** Wrong rows stay forever; a corrected vintage is inserted
   under a new `received_at`. Honest and lossless, but "what did we know on 5
   September" then returns the wrong answer for ever, which is the exact
   question the design exists to answer.
2. **Add a `superseded_by` column.** Bad rows stay but point at their
   replacement; views filter them out. No deletion, full history, one more
   column and one more thing to remember in every query.
3. **Allow a narrow, logged delete** of one `(feed_id, received_at)` slice,
   requiring a DECISIONS entry naming the bug. Simple, but it puts a hole in
   rule 1 and the hole will get used again.

CC's lean is option 2 — it keeps rule 1 literally true — but this is a change to
the core table and belongs to the design, not to the ingestor. Not urgent: it
matters the first time a parser is wrong, which has not happened. Until it is
answered, `--reparse` reports what it skipped rather than pretending to fix it.

**Answered 2026-09-11 by the owner: none of the three — a fourth option,
`parse_version`.**

> Add `parse_version INTEGER NOT NULL DEFAULT 1` to `observations` and include
> it in the primary key. A parser correction re-parses the ORIGINAL bronze file
> with the ORIGINAL `received_at` and `parse_version = previous + 1`. The bad
> rows stay forever as evidence. Nothing is updated or deleted. The fix is
> itself append-only and auditable.
>
> `observations_latest` picks `max(parse_version)` within each
> `(feed_id, series_id, entity_id, period_start, received_at)` FIRST, then
> `max(received_at)` per period.
>
> Add a small append-only table recording why: `parse_corrections`.
>
> Rules: a new `received_at` is ONLY for a fresh fetch, never for a re-parse.
> `parse_version` increments ONLY when re-parsing an existing bronze file.
> `run()` gets an optional `bronze_path` parameter: if given, skip the fetch and
> re-parse that file with the next `parse_version`.
>
> Rejected: `superseded_by` (needs UPDATE); DELETE and reinsert (destroys
> evidence); a new `received_at` (misrepresents a parser bug as a source
> revision).

Done by CC on 2026-09-11: the column and the primary key, the two-stage
`observations_latest`, the `parse_corrections` table, all three written into
DESIGN.md, and `db/migrations.py` so an existing database gains the column
without losing a row (a primary key cannot be altered in place, so it is a
rebuild inside one transaction; verified on a database holding 120 rows, two
vintages and a hand-written note). 10 tests in `tests/test_views.py`, including
the acceptance test: a wrong value at version 1 and a corrected one at version 2
both exist, and `observations_latest` shows only the corrected value.

Left for the owner's `ingest/fred.py` migration (Q2): the `bronze_path`
parameter on `run()`, looking up the next `parse_version` for a file, and
writing the `parse_corrections` row. `ingest/fred.py` today inserts by name and
takes the default of 1, so its behaviour is unchanged until then.

**Q2 (2026-09-11, CC) — Does `ingest/fred.py` get retrofitted to the new
`core/` layout, or does it stay as it is until the second ingestor?**

`docs/ARCHITECTURE.md` arrived today and specifies a `core/` package (paths,
config, a redacting logger, one HTTP helper with explicit timeouts, typed
errors), an `ingest/bronze.py`, an `ingest/runs.py` with a `RunResult`
dataclass, and an `ingest_runs` row written at the start and end of every run.

`ingest/fred.py` was written on 5 September, before any of that existed. It
works and is tested, but it does not match: it calls `httpx` directly, writes
bronze itself, raises its own `BadPayload` rather than the typed `FeedError` /
`ParseError` / `StorageError`, returns a plain tuple rather than a `RunResult`,
and writes no `ingest_runs` row — the table does not exist yet either.

Three ways forward:

1. **Build `core/` and `ingest_runs` now and move `fred.py` onto them before
   `eia.py` is written.** One ingestor to change instead of three, and the EIA
   and PortWatch ingestors get written against the standard the first time.
   Costs a refactor of working, tested code.
2. **Build `core/` now, leave `fred.py` alone, write `eia.py` against `core/`.**
   Nothing working gets touched, but the repo then has two shapes of ingestor at
   once and the FRED tests keep testing the old one.
3. **Leave all of it until `eia.py` and `portwatch.py` exist**, then extract from
   three real cases, which is what CLAUDE.md's rule about abstraction actually
   says.

CC's lean is option 1, on the grounds that `core/` is not being invented from
guesses — ARCHITECTURE.md already specifies it, so the three-cases rule is not
really in play, and doing it now is the cheapest it will ever be. But this
touches code the owner has already read and understood, so it is the owner's
call.

**Answered 2026-09-11 by the owner: option 1, with the migration split.**

> The three-cases rule in CLAUDE.md is about abstracting the SHAPE of an
> ingestor — base classes, plugin registries, generic adaptors. `core/` is not
> that. Config loading, a redacting logger, one HTTP helper with timeouts, and
> typed errors would exist in any project with one feed or fifty; they are
> shared plumbing, not an abstraction extracted from feeds. `ingest/bronze.py`
> and `ingest/runs.py` are borderline, but they exist to enforce two of the four
> unbreakable rules (bronze-before-parse, every run recorded), and rules enforced
> by shared code are stronger than rules enforced by each ingestor remembering.
> One ingestor migrating now costs an hour. Three migrating later costs a day and
> produces two shapes of ingestor in the meantime, which is the worst outcome.
>
> The owner migrates `fred.py`, not Claude Code. Owner wrote it; owner moves it.
> Claude Code reviews the diff and explains anything non-obvious. Keep the
> existing test passing throughout; add the idempotency assertion on
> `ingest_runs` (exactly one row per run, status ok).

Done by CC on 2026-09-11: `core/` (paths, errors, logging with redaction,
config, http), the `ingest_runs` table, and `ingest/runs.py` with `RunResult`,
`start_run()` and `finish_run()`. 30 new tests. CLAUDE.md's first forbidden
bullet amended as instructed. Left for the owner: moving `ingest/fred.py` onto
them. `ingest/bronze.py` is not written — see Q4.

