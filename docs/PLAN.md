# Plan — v0 (4 weeks)

Work top to bottom. Tick boxes as you go. "Owner" means you write it, with Claude
Code watching and explaining. "CC" means Claude Code writes it, you read the diff
before accepting. "Research" means the coordination chat, not Claude Code.

## Week 0 — before any code

- [x] Research: feed endpoints verified. See `docs/feeds/*.md`. PortWatch has three verify-on-first-run items listed there.
- [ ] Owner: create `docs/OBSERVATIONS.md` as a plain text stand-in for the log until the table exists. Start writing in it from the day you first look at any chart, even a chart on the EIA website.

## Week 1 — environment and first feed

- [x] Owner: install `uv`, create the repo, `uv init`, add `duckdb pandas httpx streamlit pytest python-dotenv`.
- [x] Owner: create `data/bronze/` and add `data/` to `.gitignore`.
- [x] Owner: get a free EIA API key (eia.gov/opendata). Put it in `.env`. Never commit it.
- [x] Owner: get a free FRED API key (fred.stlouisfed.org). Same.
- [x] CC: `core/` package per ARCHITECTURE.md §2: paths, config, logging with key redaction, http with explicit timeouts, typed errors. Unit tests for redaction and config. **Done 2026-09-11, 20 tests. Q2 answered: build it now.**
- [~] CC: `db/schema.sql` with all objects from DESIGN.md including `observation_log`, `split_mask`, `ingest_runs`, and the `observations_explore` / `observations_holdout` views. `db/init.py` that creates them. `db/units.md`. **`ingest_runs` added 2026-09-11. `db/units.md` still to do.**
- [~] CC: `ingest/bronze.py` (atomic write, never overwrite) and `ingest/runs.py` (RunResult, start_run, finish_run). **`ingest/runs.py` done 2026-09-11, 10 tests. `ingest/bronze.py` not written — see Q4.**
- [x] CC: `parse_version` on `observations` and in its primary key, two-stage `observations_latest`, `parse_corrections` table, `db/migrations.py`. **Q1 answered 2026-09-11; 10 tests in `tests/test_views.py`.**
- [ ] **Owner:** move `ingest/fred.py` onto `core/` and `ingest/runs.py` — `core.http.get` instead of `httpx.get`, `core.errors` instead of `BadPayload`, `core.config.api_key` instead of reading `os.environ`, `core.paths.bronze_path` instead of building the path, and `start_run()`/`finish_run()` around the whole thing so every run is recorded. Keep the 16 existing tests passing; add the `ingest_runs` assertion (exactly one row per run, status ok). CC reviews the diff and explains anything non-obvious.
- [ ] **Owner:** the Q1 half of the same migration — `run(conn, received_at=..., bronze_path=...)` skips the fetch and re-parses that file at the next `parse_version`, and writes a `parse_corrections` row saying why. The storage and views are in place and tested; this is the ingestor side.
- [x] CC: `db/make_split.py` — fixed seed, 25% of ISO weeks 2015–2030 marked holdout, writes `db/split_mask.csv`. Commit the CSV. It never changes again.
- [ ] Owner: migrate anything from `docs/OBSERVATIONS.md` into `observation_log` by hand once the table exists.
- [x] CC: `db/seed_entities.sql` with the three v0 entities and their aliases.
- [x] ~~**Owner writes** `ingest/fred.py` by hand~~ **CC wrote it, owner's call 2026-09-05.** See DECISIONS. The learning goal moves to the walkthrough and to Week 4's "explain every table and column without looking", which is unchanged.
- [x] CC: walk the owner through `ingest/fred.py` line by line.
- [ ] Milestone: `python -m ingest.fred` puts Brent and OVX rows into `observations`. Query them in the DuckDB CLI.

## Week 2 — the other two feeds and the idempotency test

- [ ] Research: confirm the exact PortWatch API endpoint and response shape for the Hormuz chokepoint series; write findings to `docs/feeds/portwatch.md`.
- [ ] Research: same for EIA crude stocks series ID (weekly, excluding SPR); `docs/feeds/eia.md`.
- [ ] CC: `ingest/eia.py` following the same shape as the owner's FRED ingestor.
- [ ] CC: `ingest/portwatch.py`. Note: PortWatch may return the full history each call. That is fine — it all gets one `received_at`, and the primary key handles it.
- [~] CC: `tests/test_idempotency.py` with fixture payloads for all three. **FRED done (16 tests, 2026-09-05); EIA and PortWatch fixtures still to add.**
- [ ] Owner: run the tests. Break one on purpose. Understand why it fails.
- [ ] CC: `Makefile` with `init`, `ingest`, `test`, `dashboard` targets.
- [ ] Milestone: `make ingest` twice in a row; row count in `observations` exactly doubles.

## Week 3 — see it

- [ ] CC: `app/dashboard.py` — three charts from `observations_explore` (never `_latest`), a table of `feed_id, max(received_at)`, a "Note this" box under each chart that writes to `observation_log` with the visible series and date range attached, and a Log page listing entries newest-first. No edit, no delete.
- [ ] Owner: verify the holdout gaps are visible in the charts. If the charts look continuous, the app is reading the wrong view.
- [ ] Owner: every day this week, look at the dashboard for ten minutes and write at least one note. Bad notes are fine. "Nothing moved" is a note.
- [ ] CC: `app/export_map.py` — CSV of entities with lat/lon.
- [ ] Owner: open Kepler.gl (kepler.gl/demo), drag the CSV in, see the Hormuz marker. Screenshot it into `docs/`.
- [ ] Owner: run `make ingest` every day this week by hand. Watch `received_at` accumulate. This is the whole point of the design and you should see it happen.
- [ ] Milestone: dashboard shows three live series and the map shows one dot.

## Week 4 — prove the design

- [ ] CC: `queries/asof.sql` — a parameterised point-in-time query: "what did we know about series X on date Y."
- [ ] Owner: run it for a date last week. Compare to today. If EIA revised anything, you will see two vintages. If not, you will see that the design supports it anyway.
- [ ] Owner: write `docs/RETRO.md` — one page. What was harder than expected, what was easier, what you now understand that you did not. Honest.
- [ ] Owner and Research together: read every entry in `observation_log`. Pick the one that is most specific and most testable — not the most exciting. That becomes the v1 claim. Everything else stays `noted`.
- [ ] Research: read RETRO.md and the chosen observation, rewrite SCOPE.md v1 section into a real plan.
- [ ] Owner: explain every table and column out loud to someone (or to Claude Code) without looking. If you cannot, v0 is not done.
- [ ] Milestone: v0 done criteria in SCOPE.md all met.

## Not in this plan, on purpose

No models. No forecasts. No agents. No scheduler. No cloud. No fourth feed.
If any of these get started during v0, stop and re-read CLAUDE.md.
