# Scope

Three tiers. v0 is fully specified. v1 is a milestone with acceptance criteria only.
Anything not listed is out of scope until v1 ships and the plan is rewritten.

## v0 — "data flows end to end" (target: 4 weeks)

**Goal.** Three free feeds land in a local database with vintage history and appear
on a chart and a map, and the owner watches them daily and logs what they notice.
This is an observation phase, not a modelling phase. No hypothesis is required to
start; the point is to arrive at one honestly.

**Timeline.** Four weeks if the owner has some Python; eight if learning from
scratch. Either is fine. The order matters, the speed does not.

**Vertical.** Energy and shipping only. Semiconductors and agriculture are v2.

**Feeds.**

| feed_id | Provider | What | Cadence | Upstream |
|---|---|---|---|---|
| `portwatch_hormuz` | IMF PortWatch | Daily vessel transits, Strait of Hormuz | Weekly release | AIS via PortWatch |
| `eia_crude_stocks` | US EIA API v2 | Weekly US crude oil stocks (excl. SPR) | Weekly, Wednesdays | EIA survey |
| `fred_brent_ovx` | FRED | Brent spot (DCOILBRENTEU), oil volatility index (OVXCLS) | Daily | ICE / CBOE via FRED |

**Storage.** DuckDB. Bronze = raw payload files, never touched. Silver = one long
table `observations` with bitemporal columns (see DESIGN.md).

**Entities.** One registry table seeded with: Strait of Hormuz (as a chokepoint
entity), United States (ISO `USA`), Brent (as a benchmark entity). That is all.

**Output.** One Streamlit page with three time-series charts and a "last received"
timestamp per feed. One Kepler.gl map with the Hormuz chokepoint marked. That is all.

**Done when:**
- `make ingest` runs all three ingestors and can be run repeatedly without
  duplicating or overwriting rows.
- Each ingestor has a passing idempotency test.
- The owner can explain every table and every column without looking.
- `docs/DECISIONS.md` has at least five entries written during the build.
- `split_mask` exists, is committed, and the dashboard cannot show holdout weeks.
- `observation_log` has at least ten entries, written on at least ten different
  days. Quantity of noticing is the v0 output, not quality.

**Known limitation.** Only EIA revises its data visibly, so v0 proves the
bitemporal plumbing exists but does not stress it. v1 must add a feed with
heavy revisions to validate the design properly.

## v1 — "a working instrument" (milestone, not yet planned)

**Goal.** Pick one entry from the observation log, state it as a testable
claim, and test it on holdout data. Learn whether it was real.

**Acceptance criteria (draft, to be firmed up when v0 ships):**
- Six or more feeds across energy and shipping, including European gas storage
  (GIE AGSI+), CFTC positioning, and at least one feed with heavy revisions.
- Scheduled daily ingestion (Prefect or Dagster — decide then).
- One observation from the log promoted to a written claim, tested with proper
  statistics on point-in-time holdout data, with a written result. A rejection
  counts as success; the process worked.
- A forecast ledger: every prediction logged with timestamp and probability,
  scored when resolved.
- Dashboard with a live map layer (aisstream Hormuz) and a 2D graph view of the oil-and-gas value chain, three to four hops, with gaps rendered red and each gap logged to QUESTIONS.md.

## Out of scope until further notice

- Trade execution of any kind, including paper trading.
- Agents. LLMs may be used for one-off extraction experiments only, by hand.
- Paid data.
- Cloud deployment.
- Semiconductors, agriculture, defence, gold.
- Anything in `PARKING_LOT.md`.
