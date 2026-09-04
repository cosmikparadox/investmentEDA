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
