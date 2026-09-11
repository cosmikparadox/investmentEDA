# Architecture — controlroom

Version 1.0 · 11 September 2026. DESIGN.md holds the v0 schema. This document
holds the structure that DESIGN.md sits inside: modules, contracts, error
handling, observability, testing, and how each later phase attaches without
rewriting what came before.

## 1. Shape

```
  ┌─────────────────────────────────────────────────────────────┐
  │ app/          Streamlit pages · map export · (v1) graph view │  presentation
  ├─────────────────────────────────────────────────────────────┤
  │ queries/      point-in-time · holdout tests · hand-run only  │  research
  ├─────────────────────────────────────────────────────────────┤
  │ db/           schema · views · init · split · migrations     │  silver
  ├─────────────────────────────────────────────────────────────┤
  │ ingest/       one module per feed · bronze writer · runs     │  bronze
  ├─────────────────────────────────────────────────────────────┤
  │ core/         paths · config · logging · http · errors       │  shared
  └─────────────────────────────────────────────────────────────┘
```

Dependencies point downward only. `app/` imports `db/` views. `ingest/`
imports `core/` and writes to `db/`. Nothing imports from `app/`. Ingestors
never import each other.

## 2. Module layout (v0)

```
controlroom/
├── core/
│   ├── paths.py        repo-relative paths; the only place that knows where data/ is
│   ├── config.py       loads .env once; exposes typed settings; raises if a key is missing
│   ├── logging.py      configures one logger per module; key=value lines; redacts keys
│   ├── http.py         get_json(url, params, timeout) with explicit timeouts and error context
│   └── errors.py       FeedError, ParseError, StorageError — all carry feed_id and context
├── ingest/
│   ├── bronze.py       write_bronze(feed_id, received_at, payload) -> path
│   ├── runs.py         start_run(), finish_run() writing ingest_runs; RunResult dataclass
│   ├── fred.py         run(conn, received_at=None) -> RunResult
│   ├── eia.py          same signature
│   └── portwatch.py    same signature
├── db/
│   ├── schema.sql      all tables and views
│   ├── init.py         creates schema; seeds entities and feeds; idempotent
│   ├── seed_entities.sql
│   ├── seed_feeds.sql
│   ├── make_split.py   writes split_mask.csv from a fixed seed
│   ├── split_mask.csv  committed; never regenerated
│   └── units.md        the canonical unit list
├── queries/
│   ├── asof.sql        point-in-time query
│   └── tests/          one .sql per tested observation (v1)
├── app/
│   ├── dashboard.py    the one page
│   ├── log_page.py     read-only observation log
│   └── export_map.py   entities → CSV for Kepler.gl
├── tests/
│   ├── fixtures/       one saved payload per feed
│   ├── test_idempotency.py
│   ├── test_views.py
│   └── test_core.py
├── data/               gitignored: bronze/, controlroom.duckdb
├── docs/               everything you are reading
├── Makefile            init · ingest · test · check · dashboard
├── pyproject.toml
├── .env.example
└── CLAUDE.md
```

Rule: an ingestor is a plain module with one public function. Shared
behaviour (bronze writing, run recording, HTTP) lives in `ingest/bronze.py`,
`ingest/runs.py`, `core/http.py` as functions, not base classes. If three
ingestors turn out to share a shape, extract it in v1 with a DECISIONS.md
entry. Not before.

## 3. Contracts

### 3.1 Ingestor contract

```python
def run(conn: duckdb.DuckDBPyConnection, received_at: datetime | None = None) -> RunResult:
    """Fetch this feed, persist raw payload, parse, insert observations.

    received_at defaults to now (UTC). Passing it explicitly is for tests and
    for replaying bronze files. Returns a RunResult; never raises for a feed
    failure — failures are recorded and returned. Raises only for programmer
    errors (bad schema, missing config).
    """
```

```python
@dataclass(frozen=True)
class RunResult:
    feed_id: str
    received_at: datetime
    status: Literal["ok", "failed"]
    rows_fetched: int
    rows_inserted: int       # after ON CONFLICT DO NOTHING
    bronze_path: str | None
    error: str | None        # redacted, first 500 chars
    duration_s: float
```

Inside `run`, the order is fixed and must not be reordered:

1. `start_run()` — writes an `ingest_runs` row with status `running`.
2. Fetch — via `core.http.get_json`. On failure: `finish_run(failed)`, return.
3. `write_bronze()` — raw payload to disk. On failure: `finish_run(failed)`, return. **This happens before any parsing.**
4. Parse — pure function `parse(payload, received_at) -> list[Observation]`. On failure: `finish_run(failed, bronze_path=...)`, return. The bronze file survives.
5. Insert — one transaction, `INSERT ... ON CONFLICT DO NOTHING`. On failure: rollback, `finish_run(failed)`, return.
6. `finish_run(ok, rows_inserted=...)`, return.

### 3.2 Parse contract

`parse()` is a pure function: payload in, list of typed rows out, no I/O, no
clock, no database. This is what makes it unit-testable against a fixture.
The `received_at` is passed in, never read from `now()` inside parse.

### 3.3 Bronze contract

`write_bronze(feed_id, received_at, payload: bytes) -> Path`. Writes to a
temp file then atomically renames, so a crash never leaves a half-written
bronze file. Never overwrites: if the path exists, raises `StorageError`.

### 3.4 Storage contract

- Inserts only, via parameterised SQL. No string-formatted SQL anywhere.
- One transaction per run.
- Primary key on `observations` includes `received_at`; the database enforces
  rule 1, the code does not merely promise it.

### 3.5 View contract (what the app may touch)

- `app/` reads `observations_explore`, `observation_log`, `ingest_runs`,
  `entity_registry`, `feed_registry`, and (v1) `edges`, `live_positions`.
- `app/` never reads `observations`, `observations_latest`, or
  `observations_holdout`. Enforced by a test that greps `app/` for those names.

## 4. Error handling strategy

Three error classes in `core/errors.py`, all subclasses of `ControlroomError`:

| Class | Raised when | Carries |
|---|---|---|
| `FeedError` | HTTP failure, timeout, auth rejection, unexpected shape | feed_id, url (redacted), status, body[:500] |
| `ParseError` | Payload does not match expected schema | feed_id, bronze_path, field, sample |
| `StorageError` | Bronze write or DB insert fails | feed_id, path or table, underlying message |

Rules:
- Never `except:` or `except Exception:` without re-raising or converting to a
  typed error with context. Silent failure is the worst outcome in this system
  because it corrupts the record of what was known when.
- `run()` catches typed errors, records them in `ingest_runs`, and returns a
  failed `RunResult`. It does not catch programmer errors (KeyError from a
  typo, ImportError) — those should crash loudly during development.
- `make ingest` calls every ingestor, collects results, prints a table, exits
  1 if any failed. One bad feed never blocks the others.
- Every error message a human might read is written so the owner can act on
  it: what failed, for which feed, what to check.

## 5. Observability

- `ingest_runs` table: `run_id, feed_id, received_at, started_at, finished_at,
  status, rows_fetched, rows_inserted, bronze_path, error`. Written at start
  and end. This is the operational history of the system and the first thing
  to look at when something is wrong.
- Logging: `core/logging.py` sets a root format of
  `ts=… level=… module=… feed=… msg=…`. Level from `LOG_LEVEL` in `.env`,
  default INFO. Keys redacted by a filter that replaces any value matching a
  configured key with `***`.
- Dashboard: a "Runs" panel showing the last 20 `ingest_runs` rows with status
  colouring. If the newest run for any feed is older than 2× its cadence, the
  panel says so.

## 6. Configuration

One `.env`, loaded once by `core/config.py` into a frozen dataclass:

```
EIA_API_KEY=
FRED_API_KEY=
LOG_LEVEL=INFO
DB_PATH=data/controlroom.duckdb
```

Missing required keys raise at import time with a message naming the key.
No other configuration mechanism exists in v0.

## 7. Testing strategy

| Layer | Test | Runs against |
|---|---|---|
| `core/` | unit tests for redaction, path resolution, config errors | nothing external |
| `ingest/*.parse` | fixture payload → expected rows; malformed fixture → `ParseError` | saved JSON fixtures |
| `ingest/*.run` | idempotency: run twice same `received_at` → 0 new rows; run with later `received_at` → rows doubled; original rows byte-identical | temp DuckDB, mocked HTTP |
| `db/` | views: explore ∪ holdout = latest, explore ∩ holdout = ∅; as-of query returns older vintage when a later one exists | temp DuckDB with synthetic data |
| `app/` | grep test: forbidden view names absent from `app/` | source tree |
| Makefile | `make check` = ruff + pytest; must pass before any commit that touches code | — |

Network is never hit in tests. Every ingestor's HTTP call goes through
`core.http.get_json`, which is the one thing tests patch.

## 8. Failure modes and what the design does about them

| Failure | Consequence without the design | What catches it |
|---|---|---|
| Source revises a number silently | Backtests use future information | Bitemporal PK; as-of query |
| Parser bug discovered months later | History lost | Bronze files; re-parse from bronze with original `received_at` |
| Two feeds are really one source | False confirmation | `feed_registry.upstream` (v0 text; v1 factor graph) |
| Owner studies data then tests on it | Confirmed noise | `split_mask` hidden from UI |
| Owner remembers hits, forgets misses | Overconfidence | Immutable `observation_log` |
| API key leaks into a log or commit | Key revoked, account suspended | Redaction filter; `.gitignore`; no keys in error text |
| Ingest crashes mid-write | Partial rows | One transaction per run; atomic bronze rename |
| Feed API changes shape | Silent zeros or crash | `ParseError` with sample; bronze preserved; run recorded failed |
| Live consumer dies overnight | Lost positions | Own process; reconnect with backoff; staleness shown in UI |
| Build agent over-engineers | Months lost to infrastructure | CLAUDE.md forbidden list; three-cases rule for abstraction |

## 9. How later phases attach

None of these change v0 tables or code paths. Each adds.

### v1
- **Scheduler.** Prefect or Dagster wrapping the existing `run()` functions.
  The functions do not change. Decision at v1 start (Dagster's asset model is
  a natural fit for a data-as-asset framing; Prefect is simpler).
- **Retries.** Added inside `core/http.py` only. Ingestors unchanged.
- **Live layer.** `live/aisstream.py`: separate process, websocket, writes
  `live_positions(imo, mmsi, lat, lon, sog, cog, received_at)` in
  micro-batches. Own table, own process, own log. Dashboard reads it.
- **Edges and graph.** `edges` table per DESIGN.md. `app/graph_page.py` with a
  force-directed layout (e.g. `pyvis`/`networkx` or a small D3 component).
  Gap creation calls `research/questions.py` to append to `QUESTIONS.md`.
- **Forecast ledger.** `forecasts` table; `queries/score.sql` for Brier.
- **Data contracts.** Pandera schemas on parse output, added after the first
  silent bad-data incident, which will happen.

### v2
- **Features (gold).** `features/` package: pure functions from
  `observations_explore` to aligned, resampled frames. Point-in-time joins
  across mixed frequencies. Stored in a `features` table keyed by
  `(feature_id, period, computed_at, asof)`.
- **Models.** `models/` package. Every model has a `tier` field (T1/T2/T3)
  and a runtime guard: T3 outputs cannot be written to any table the app
  reads. Nowcasting (dynamic factor + Kalman) and regime detection first.
- **LLM extraction.** `extract/` package: LLM turns a PDF or article into
  candidate rows; every row lands with `status='inferred'` and a `source`
  pointing at the document; a human promotes or rejects. Never writes
  `observed`.

### v3+
- **Agents.** Orchestration over the deterministic tools above. Agents choose
  which tool to run and explain results; they never compute numbers.
  Adversary agent runs before any claim is promoted.
- **3D graph.** Only if the 2D graph is demonstrably insufficient.
- **Postgres / Timescale.** When concurrent writers exist. Schema is already
  ANSI-leaning; migration is a script, not a redesign.

## 10. What this architecture deliberately does not have

- No message queue. One producer per feed, one consumer. Polling on a timer
  covers every batch feed; one websocket covers the live one.
- No ORM. SQL is short, visible, and the schema is the documentation.
- No plugin system. Adding a feed is: write `docs/feeds/x.md`, write
  `ingest/x.py`, add a row to `seed_feeds.sql`, add a fixture and test.
- No cloud. A `docker-compose.yml` is the most that v1 adds, so the same
  thing runs on a £5 VM when uptime matters.
- No execution layer. Ever.
