# CLAUDE.md — read this before touching anything

This repo is a personal commodity and supply-chain intelligence system, built by
someone new to trading and data engineering who is learning by building.
You are pairing, not delegating. The owner runs commands and reads diffs.

## Source of truth

The repo is the memory. Nothing decided in a chat counts until it is written here.

- `docs/SCOPE.md` — what is in v0, v1, and what is parked. Do not expand it.
- `docs/DESIGN.md` — the architecture. Follow it. Propose changes in `docs/QUESTIONS.md`.
- `docs/PLAN.md` — the task list. Work top to bottom. Tick things off.
- `docs/DECISIONS.md` — append a dated entry every time you make a non-trivial choice.
- `docs/QUESTIONS.md` — write questions here instead of guessing. A separate
  research session answers them.
- `docs/PARKING_LOT.md` — ideas deferred until after v1. Do not implement anything in it.

## Three rules that cannot be broken

1. **Never overwrite ingested data.** Every row carries `received_at`. Re-running an
   ingestor appends a new vintage; it does not update or delete. If a source revises
   a value, both the old and new rows exist.
2. **Every feed declares its upstream source in plain text** (`upstream` column in
   `feed_registry`). "AIS via IMF PortWatch", "EIA survey", "ICE settlement via FRED".
3. **Ships, ports, companies and countries use canonical IDs** — IMO number,
   UN/LOCODE, LEI, ISO 3166-1 alpha-3. Names are aliases, never keys.
4. **The dashboard never renders holdout periods.** A deterministic slice of
   history (`split_mask`) is hidden from every exploration view so that patterns
   noticed by eye can later be tested on data nobody has looked at. There is no
   "show everything" toggle in the app. Holdout is reachable only through
   `queries/` by hand, and only when testing a logged observation.

## Forbidden until v1 is shipped

Do not build any of the following, even if it seems obviously useful:

- Abstract base classes, plugin registries, or a "framework" for feed adaptors.
  Each ingestor is a plain Python function. Duplication is fine at this stage.
- Configuration systems beyond a single `.env` file.
- Any scheduler beyond a `Makefile` target run by hand. Prefect/Dagster is v1.
- Any model, forecast, backtest, signal, or agent. v0 is data in, data visible.
- Any cloud deployment. Local only.
- Any paid data feed.
- Anything in `docs/PARKING_LOT.md`.

If you believe one of these is genuinely needed, write the case in `docs/QUESTIONS.md`
and stop. Do not proceed on your own judgement.

## Stack (fixed for v0)

- Python 3.12, managed with `uv`. No conda, no poetry.
- DuckDB, single file at `data/controlroom.duckdb`.
- Raw payloads land as files under `data/bronze/<feed_id>/<received_at>.json` before
  anything is parsed. Parsing failures must never lose the raw payload.
- `pandas` for transforms. `httpx` for HTTP. `pytest` for tests.
- Streamlit for the single dashboard page. Kepler.gl via exported CSV for the map.
- No ORM. SQL lives in `.sql` files or plain strings.

## How to work

- Small commits with plain messages saying what changed and why.
- Every ingestor gets one test: run it twice, assert row count doubles and no row
  was modified.
- When something is unclear, prefer the boring option and note it in `docs/DECISIONS.md`.
- Do not refactor code you were not asked to touch.
- Do not add dependencies without noting them in `docs/DECISIONS.md`.

## Owner's learning goals

The owner wants to understand what is built. When you write non-obvious code, add a
short comment saying what it does in plain terms. Assume no prior knowledge of
trading, market data, or data engineering conventions. Define jargon the first time
it appears in any file.
