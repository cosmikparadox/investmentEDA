# Product requirements — controlroom

Version 1.0 · 11 September 2026. Requirements are numbered so DECISIONS.md and
tests can cite them. "Must" = required for the phase's exit. "Should" = build
if cheap, otherwise log to PARKING_LOT.md. Phase tags: [v0] [v1] [v2].

## 1. Users

One user: the owner. Two modes of use.

- **Explorer.** Opens the app daily, looks at charts and the map, writes notes.
  Needs speed, clarity, and honesty about what is and isn't known.
- **Researcher.** Periodically tests a logged observation against holdout
  data, curates graph edges, fills gaps. Needs point-in-time queries and a
  clear record of provenance.

## 2. User stories

- [v0] As an explorer, I open one page and see the three series with the date
  of their last update, so I know the data is fresh.
- [v0] As an explorer, I see visible gaps in the charts where holdout weeks
  are, so I cannot accidentally study data I'm supposed to test on later.
- [v0] As an explorer, I type a sentence under a chart and it is saved with
  the date and what I was looking at, so my noticing is recorded before I
  check it.
- [v0] As a researcher, I ask "what did we know about series X on date D" and
  get the answer, so backtests use only information available at the time.
- [v1] As an explorer, I see ships moving through Hormuz on the map, live.
- [v1] As an explorer, I pick a central entity and see its graph, with gaps in
  red, so I know where my picture of the world has holes.
- [v1] As a researcher, I promote one logged observation to a claim, run it
  against holdout, and record supported or rejected.
- [v1] As a researcher, every red edge already exists as a question I can
  hand to the research session.

## 3. Functional requirements

### 3.1 Ingestion

| ID | Requirement | Phase | Acceptance |
|---|---|---|---|
| FR-01 | One ingestor module per feed, exposing `run(conn, received_at=None) -> RunResult` | v0 | Three modules exist; each callable independently |
| FR-02 | Raw payload written to bronze before parsing | v0 | Bronze file exists even when parse raises |
| FR-03 | Parsed rows inserted with `ON CONFLICT DO NOTHING` on the full primary key including `received_at` | v0 | Re-run with same `received_at` inserts zero rows; later `received_at` appends |
| FR-04 | No UPDATE or DELETE statement anywhere against `observations` | v0 | Grep of codebase finds none; test asserts original rows byte-identical after re-run |
| FR-05 | Every run recorded in `ingest_runs` with feed, start, end, status, rows_inserted, error text | v0 | Table populated for success and failure |
| FR-06 | Missing values preserved as NULL, never dropped or zero-filled | v0 | FRED "." becomes NULL and the row exists |
| FR-07 | `make ingest` runs all ingestors, continues past a failure, exits non-zero if any failed | v0 | One ingestor mocked to fail; others still run; exit code 1 |
| FR-08 | Scheduled ingestion on a timer per feed cadence | v1 | Runs unattended for 7 days with no manual intervention |
| FR-09 | One live websocket consumer (aisstream) in its own process writing to its own table | v1 | Killing it does not affect batch ingestion; restart resumes |
| FR-10 | Retry with exponential backoff on HTTP 429/5xx; give up after N attempts and record failure | v1 | Test with mocked 429 sequence |

### 3.2 Storage

| ID | Requirement | Phase | Acceptance |
|---|---|---|---|
| FR-20 | `observations` table per DESIGN.md with bitemporal columns | v0 | Schema matches; PK includes `received_at` |
| FR-21 | `entity_registry` and `entity_alias` per DESIGN.md | v0 | Seeded with three entities |
| FR-22 | `feed_registry` with mandatory `upstream` text | v0 | Three rows; `upstream` non-empty |
| FR-23 | `observation_log` append-only | v0 | No UPDATE/DELETE path in code; status transitions forward only |
| FR-24 | `split_mask` generated once, fixed seed, committed as CSV | v0 | File in git; regenerating produces identical file |
| FR-25 | `observations_latest`, `observations_explore`, `observations_holdout` views | v0 | Explore ∪ holdout = latest; explore ∩ holdout = ∅ |
| FR-26 | `ingest_runs` table | v0 | See FR-05 |
| FR-27 | `edges` table per DESIGN.md v1 section | v1 | Every row has non-empty `source` |
| FR-28 | `forecasts` ledger: claim, probability, made_at, resolves_at, outcome, score | v1 | One resolved row with Brier score computed |

### 3.3 Application

| ID | Requirement | Phase | Acceptance |
|---|---|---|---|
| FR-40 | Single Streamlit page: three charts from `observations_explore` | v0 | Charts render; holdout weeks visibly absent |
| FR-41 | "Last received" table: feed_id, max(received_at), row count | v0 | Present and correct |
| FR-42 | "Note this" input under each chart writes to `observation_log` with visible series and date window attached | v0 | Row created with correct `series_ids`, `window_start`, `window_end` |
| FR-43 | Log page listing entries newest first with status; no edit or delete controls | v0 | No mutation controls present |
| FR-44 | App never imports or queries `observations_latest` or `observations_holdout` | v0 | Grep of `app/` finds neither |
| FR-45 | Map: CSV export of entities with coordinates for Kepler.gl | v0 | File produced; one Hormuz row |
| FR-46 | Live map layer from aisstream table | v1 | Positions update without page reload or within 60s refresh |
| FR-47 | 2D force-directed graph view: select central entity, render neighbours from `edges` | v1 | Renders ≥10 nodes; click isolates a chain |
| FR-48 | Edge rendering by status: observed / inferred / gap, gap visibly red, legend present | v1 | Colour-blind-safe secondary cue (dash pattern) also present |
| FR-49 | Clicking a gap edge shows `gap_reason`, `gap_status`, and a link to its QUESTIONS.md entry | v1 | Works for every gap edge |

### 3.4 Research support

| ID | Requirement | Phase | Acceptance |
|---|---|---|---|
| FR-60 | Parameterised point-in-time query: series, as-of date → values known at that date | v0 | Returns older vintage when a revision exists after the as-of date |
| FR-61 | Holdout queries live only under `queries/` and are run by hand | v0 | No app code path reaches them |
| FR-62 | Creating a `gap` edge appends a templated entry to `docs/QUESTIONS.md` | v1 | Entry contains edge_id, from, to, relation, gap_reason |
| FR-63 | Observation lifecycle: noted → testing → supported/rejected, with `test_ref` path | v1 | One full lifecycle completed |

## 4. Data requirements

| ID | Requirement |
|---|---|
| DR-01 | Every observation row: `feed_id, series_id, entity_id, period_start, period_end, value, unit, received_at, source_asof, bronze_path` |
| DR-02 | `received_at` is UTC, set once per run, identical across all rows of that run |
| DR-03 | `entity_id` format: `<type>:<canonical>` e.g. `chokepoint:hormuz`, `country:USA`, `benchmark:brent`, `vessel:IMO9876543`, `port:AEFJR` |
| DR-04 | Units are canonical strings from a fixed list in `db/units.md`; new units require a DECISIONS.md entry |
| DR-05 | Bronze path: `data/bronze/<feed_id>/<received_at ISO, colons→dashes>.json` |
| DR-06 | Every feed spec in `docs/feeds/<feed_id>.md` before its ingestor is written |
| DR-07 | Licence and attribution string recorded in `feed_registry.license_notes` |
| DR-08 | [v1] Every edge: `source` non-empty; `status` in {observed, inferred, gap}; if gap, `gap_reason` and `gap_status` non-empty |

## 5. Non-functional requirements

### 5.1 Reliability and error handling

| ID | Requirement |
|---|---|
| NFR-01 | An ingestor failure never loses the raw payload (bronze written first) |
| NFR-02 | An ingestor failure never leaves partial rows: parse fully in memory, then insert in one transaction |
| NFR-03 | Errors are raised with context: feed_id, URL (keys redacted), HTTP status, first 500 chars of body |
| NFR-04 | No bare `except:`. No swallowed exceptions. Catch specific exceptions, record, re-raise or return a failed `RunResult` |
| NFR-05 | HTTP timeouts set explicitly on every request (connect 10s, read 60s) |
| NFR-06 | [v1] Retries: exponential backoff with jitter, max 5 attempts, only on 429/5xx/timeouts, never on 4xx other than 429 |
| NFR-07 | [v1] Live consumer reconnects on disconnect with backoff; buffers nothing in memory beyond one message |

### 5.2 Idempotency and correctness

| ID | Requirement |
|---|---|
| NFR-10 | Running any ingestor twice with the same `received_at` is a no-op |
| NFR-11 | Running with a later `received_at` appends and never modifies |
| NFR-12 | All timestamps UTC; all dates ISO 8601; no naive datetimes in the database |
| NFR-13 | Numeric parsing is explicit (`float(x)`), never implicit; strings from APIs are never stored as numbers without conversion |

### 5.3 Observability

| ID | Requirement |
|---|---|
| NFR-20 | Structured logging via `logging` module, one logger per module, JSON-ish key=value lines, level configurable via `.env` |
| NFR-21 | `ingest_runs` row for every run; dashboard shows last 20 runs with status |
| NFR-22 | Log lines never contain API keys |

### 5.4 Performance

| ID | Requirement |
|---|---|
| NFR-30 | Dashboard first render under 2s with one year of data for three series |
| NFR-31 | Full history ingest of one feed under 60s |
| NFR-32 | [v1] Graph view renders 200 nodes / 500 edges interactively |
| NFR-33 | DuckDB single file; migration to Postgres documented in ARCHITECTURE.md, not built |

### 5.5 Security

| ID | Requirement |
|---|---|
| NFR-40 | API keys only in `.env`; `.env` in `.gitignore`; `.env.example` committed with empty values |
| NFR-41 | No keys in logs, bronze filenames, or error messages |
| NFR-42 | Outbound requests only to the endpoints listed in `feed_registry` |

### 5.6 Maintainability

| ID | Requirement |
|---|---|
| NFR-50 | Module layout per ARCHITECTURE.md; no cross-imports between ingestors |
| NFR-51 | Every public function has a docstring in plain language stating what it does and what it returns |
| NFR-52 | Type hints on all function signatures |
| NFR-53 | `ruff` for lint and format; `pytest` for tests; both in `make check` |
| NFR-54 | Test coverage: every ingestor has a fixture-based idempotency test; every view has a query test; every transform has a unit test |
| NFR-55 | No dependency added without a DECISIONS.md entry |

### 5.7 Portability

| ID | Requirement |
|---|---|
| NFR-60 | Runs on macOS, Linux and Windows (WSL) with `uv` and Python 3.12 |
| NFR-61 | No absolute paths; all paths relative to repo root via a single `paths.py` |
| NFR-62 | SQL is DuckDB-flavoured but kept ANSI where possible; DuckDB-specific syntax flagged in comments |

## 6. UI requirements

| ID | Requirement | Phase |
|---|---|---|
| UI-01 | Holdout gaps in charts are visually obvious (breaks in the line), not interpolated | v0 |
| UI-02 | Every chart labelled with series_id, unit, source feed, last received | v0 |
| UI-03 | "Note this" is one text input and one button; nothing else | v0 |
| UI-04 | Log page is read-only | v0 |
| UI-05 | Edge status colours: observed = neutral, inferred = amber-ish, gap = red; plus dash patterns so colour is not the only cue | v1 |
| UI-06 | Graph legend always visible | v1 |
| UI-07 | Live layer shows staleness: "last position 42s ago" | v1 |
| UI-08 | No "show all" control anywhere, ever | all |

## 7. Out of scope

See CHARTER.md §6 and PARKING_LOT.md. Any requirement not listed here is
out of scope for its phase. Claude Code: if a requirement seems missing,
write it to QUESTIONS.md; do not infer it.
