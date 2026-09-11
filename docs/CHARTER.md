# Project charter — controlroom

Version 1.0 · 11 September 2026 · Owner: Abhineet · Status: approved for v0 build

## 1. Purpose

Build a personal data-exploration tool for commodity and supply-chain
intelligence, starting with oil and gas, that lets the owner watch real
data over time, notice patterns, log them honestly, and later test them
on data they have not seen. The tool exists to support slow, discretionary
investment decisions and to accumulate a dataset that becomes more valuable
the longer it runs.

## 2. Problem statement

Information about physical commodity flows is scattered across dozens of
free and paid sources at different cadences and lags, with no consumer tool
that consolidates it on a map, tracks how published numbers get revised, or
distinguishes what is known from what is guessed. Retail participants act on
headlines, chase moves that have already happened, and lose money at
documented rates (~70% of UK CFD accounts). The owner wants to act on data
instead, and to build the skills to do so by building the tool.

## 3. Vision (target state, not v0)

The owner selects a central entity — a commodity, a country, a company, a
chokepoint — and sees its ecosystem as a graph: the things that depend on it
and the things it depends on. Clicking an edge isolates a value chain and
shows the companies and commodities along it. A map underneath carries the
physical flows that can be observed live (tankers, ports, pipelines). Every
edge in the graph carries a status: observed from a feed, inferred by
reasoning, or a gap that nobody has data for. Gaps are rendered in red and
each one is a standing research question. Over time the red map is the
honest picture of the owner's information position.

Later phases layer statistical models (mixed-frequency nowcasting, regime
detection, lead-lag testing) and LLM capabilities (extraction from unstructured
sources, monitoring, research synthesis) on top of the data. Trade execution
is permanently out of scope.

## 4. Goals

- **G1 — Observe.** See real commodity data move, daily, in one place, on a
  map and in charts.
- **G2 — Remember correctly.** Never lose what a source said at the time it
  said it. Every number carries when it was received.
- **G3 — Be honest about ignorance.** Represent gaps in coverage explicitly
  and visibly. Never smooth over what is not known.
- **G4 — Learn by building.** The owner understands every table, column and
  module and can explain the system without notes.
- **G5 — Accumulate an asset.** The stored vintage history and the curated
  graph are the durable output. The application is replaceable.
- **G6 — Support slow decisions.** Enable long-horizon, discretionary
  investment views. Never automate a trade.

## 5. Objectives (measurable)

| ID | Objective | Measure | Phase |
|---|---|---|---|
| O1 | Three free feeds ingested with vintage history | `make ingest` idempotent; row count doubles on re-run; zero overwrites | v0 |
| O2 | One dashboard, one map | Three charts, one entity dot, holdout weeks visibly absent | v0 |
| O3 | Observation habit established | ≥10 log entries on ≥10 distinct days | v0 |
| O4 | Owner comprehension | Owner explains every table/column unprompted | v0 |
| O5 | Six+ feeds, scheduled, one live | Daily automated pulls; aisstream Hormuz layer live | v1 |
| O6 | First graph | ≥10 entities, ≥15 edges, gaps rendered red, each gap in QUESTIONS.md | v1 |
| O7 | First tested claim | One logged observation tested on holdout with written result | v1 |
| O8 | Second vertical | Semiconductor or agriculture feeds added without schema change | v2 |

## 6. Non-goals (permanent or until explicitly reopened)

- Trade execution, including paper trading. Permanent.
- Autonomous agents making decisions. Permanent.
- Paid data, until a named recurring decision is blocked without it.
- Cloud deployment, until 24/7 uptime is needed and a laptop cannot provide it.
- Sub-minute market data. The owner is not day trading.
- Multi-user, auth, sharing. Single-owner tool.
- Pricing or selling data products. Blocked on unfinished theory; not a build concern.

## 7. Principles

### 7.1 Data principles (the four unbreakable rules)
1. Ingested data is never overwritten. Every row has `received_at`. Revisions append.
2. Every feed declares its upstream source in plain text.
3. Ships, ports, companies, countries use canonical IDs. Names are aliases.
4. A deterministic holdout slice is hidden from every exploration view. There is no "show all".

### 7.2 Engineering principles
- **Boring by default.** Prefer the simplest thing that works. Complexity must be justified in DECISIONS.md.
- **Modular, not abstract.** Modules have single responsibilities and clear inputs/outputs. Abstractions are extracted only after three concrete cases exist.
- **Fail loud, lose nothing.** Errors surface immediately with context. Raw payloads are persisted before any parsing so a failure is recoverable.
- **Idempotent by construction.** Every ingestor can be re-run safely. Every transformation is a pure function of its inputs.
- **Observable.** Every run is recorded: what ran, when, how long, how many rows, what failed.
- **Testable.** Every ingestor has a fixture and an idempotency test. Every transform has a unit test.
- **Configuration in one place.** A single `.env`. No configuration frameworks.
- **Local first, portable always.** Runs on a laptop. Nothing assumes a cloud. Migration paths are documented, not built.
- **Plain language in code.** Comments explain what and why in words a beginner can follow. Jargon is defined where it appears.

### 7.3 Process principles
- The repo is the source of truth. Chat decides nothing until written down.
- One thing at a time. Finish the milestone before touching the next.
- Every non-trivial choice gets a dated entry in DECISIONS.md.
- Questions go to QUESTIONS.md, not into guesses.
- The owner writes the first instance of each new kind of thing.

## 8. Phases

| Phase | Name | Scope | Exit criterion |
|---|---|---|---|
| v0 | Observe | 3 feeds, DuckDB, dashboard, map, observation log, holdout | O1–O4 met; RETRO.md written |
| v1 | Instrument | 6+ feeds, scheduler, aisstream live, edges table + 2D graph with gaps, forecast ledger, one tested claim | O5–O7 met |
| v2 | Extend | Second vertical; nowcasting engine; regime detection; first LLM extraction | O8 met; models pass tier discipline |
| v3+ | Intelligence | Multi-agent research layer over deterministic tools; 3D graph if warranted | Defined at v2 retro |

v0 is fully specified in SCOPE.md and PLAN.md. v1 has a schema and acceptance
criteria. v2+ are direction only.

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Dashboard-with-no-hypothesis: infrastructure built, nothing learned | High | High | Observation log mandatory from day 1; v1 requires a tested claim |
| Over-engineering by the build agent | High | Medium | CLAUDE.md forbidden list; abstraction only after three cases |
| Seeing patterns in noise | High | High | Holdout mask hidden from UI; test only on holdout |
| Feed API changes or dies | Medium | Medium | Bronze raw files; ingestor per feed; upstream recorded |
| PortWatch data degraded by AIS spoofing | Certain | Medium | Treat as first construct-stability case; log it; do not model on it alone |
| Owner loses interest during plumbing phase | Medium | High | Daily observation habit gives a reason to open the app; v0 kept to weeks |
| Graph edges rendered as facts | High | High | Status on every edge; gaps red; source mandatory |
| Scope creep toward execution | Medium | High | Permanent non-goal; advisor pushes back |

## 10. Governance

- **Owner:** decides scope, writes first instances, keeps the observation log.
- **Build session (Claude Code):** implements PLAN.md, writes DECISIONS.md and QUESTIONS.md, never expands scope.
- **Research session (claude.ai project):** answers QUESTIONS.md, researches gaps, reviews output, rewrites plans at milestones.
- **Change control:** SCOPE.md changes only at a milestone retro. Any mid-phase scope change requires a DECISIONS.md entry with the reason.
