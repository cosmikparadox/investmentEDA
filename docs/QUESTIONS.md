# Questions

Claude Code writes questions here instead of guessing. The research/coordination
session answers them and marks them resolved. Keep the resolved ones; they are
part of the record.

## Open

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

## Resolved

_(none yet)_
