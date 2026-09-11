# Parking lot

Things deliberately not built. Each has a note on what would trigger revisiting it.
Claude Code: do not implement anything here. If something here seems needed,
write to QUESTIONS.md.

## Infrastructure

- **Scheduler (Prefect / Dagster).** Trigger: v1. Note Dagster's asset-oriented
  model may suit a data-as-asset framing; decide then, not now.
- **Postgres / TimescaleDB.** Trigger: concurrent writes or DuckDB file > ~10 GB.
- **Cloud VM.** Trigger: need for 24/7 ingestion that a laptop cannot provide.
- **Data-quality contracts (Pandera / Great Expectations).** Trigger: first
  silent bad-data incident. Will happen. Not yet.
- **Feed adaptor abstraction.** Trigger: sixth feed, once the shape is obvious.

## Data

- **GIE AGSI+ European gas storage.** v1 feed.
- **CFTC Commitments of Traders.** v1 feed.
- **OPEC MOMR (PDF parse).** v1 or v2. First LLM-extraction experiment candidate.
- **aisstream.io live AIS.** v1 — the one live feed. Hormuz bounding box, own process, own table.
- **GDELT news.** v2. Enormous; needs its own design.
- **Semiconductors: TSMC monthly, Taiwan MOF, Korea 20-day.** v2.
- **Agriculture: USDA NASS, WASDE, CONAB.** v2.
- **Any paid feed.** Trigger: a specific, recurring decision blocked by missing
  data. If the decision cannot be named, do not buy the feed.

## Analytics

- **Mixed-frequency nowcasting (dynamic factor model + Kalman filter).** v1 or v2.
  The right tool for daily/weekly/monthly data with different lags.
- **Lead-lag testing (Granger, transfer entropy, cointegration).** v1, one
  hypothesis only.
- **Regime detection (HMM, change-point).** v2.
- **Multiple-testing correction (deflated Sharpe).** Required the moment more than
  one hypothesis is tested. Not before.
- **Forecast ledger with Brier scoring.** v1.

## From the infonomics framework (primer v1.1, §14)

Deferred, not rejected. Revisit at the v1 retro with real data. Everything below
is listed with the primer's own epistemic tier.

- **Admissibility tests A1–A5 as a feed-registration gate** [T2-as-definition].
  A5 (construct-stability tripwire) is the valuable one. Trigger: first case
  where a feed's meaning changes while its numbers look fine. PortWatch under
  AIS spoofing is the likely first instance.
- **Provenance-to-factor graph and HHI across feeds** [T2]. Upgrades the
  free-text `upstream` column to a computed concentration measure. Trigger:
  more than ~8 feeds.
- **VoI cadence Δ* = √(2c/(k·d²)) as the scheduler rule** [T2]. Trigger: a
  scheduler exists.
- **Tier label (T1/T2/T3) on every model and signal, enforced at runtime** —
  T3 may not drive a decision. Trigger: first model.
- **Fold constraint on the regime classifier** (no bounce-back state after a
  genuine fold) [T1]. Trigger: regime detection is built.
- **Critical slowing down as early warning** (rising lag-1 autocorrelation and
  variance) [T1]. Trigger: regime detection.
- **Hawkes with mandatory Ogata residuals; n* as contagion fraction;
  aggregation-inflation caveat** [T1]. Trigger: v2. Note §14.4: daily-resolution
  Hawkes fits are something the framework itself needs — potential contribution
  back.
- **Small-gain ρ(Γ) < 1 for model-on-model stability** [T1]. Trigger: two models
  feeding each other.
- **With-and-without valuation of own feeds and models (B.1) and A.5 depreciation
  drivers.** Trigger: when it is worth asking what the accumulated dataset is
  worth. Note: Layer C is dead, so there is no framework method for *pricing*
  data products for sale. Only for valuing held assets.

## Explicitly not transferring (primer §14.3)

Recorded so nobody resurrects them:

- The φ_ij conjecture. T3, untestable, not for products.
- The USL cubic as a price model. Category error.
- Layer C in any prior form. Dead.
- Any calibration numbers from the primer's worked examples. Enterprise
  fictions, not market parameters.
- Any claim that the framework generates trading signals. It does not.

## Product

- **Agents of any kind.** Trigger: v1 shipped, and a specific, repeated manual
  task identified that an LLM does well (extraction, monitoring, summarising).
  Never decision-making.
- **Data products / pricing.** Blocked on Layer C rebuild. Not a v1 or v2 concern.
- **Execution.** Never in this plan.
