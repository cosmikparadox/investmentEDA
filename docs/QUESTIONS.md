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

## Resolved

_(none yet)_
