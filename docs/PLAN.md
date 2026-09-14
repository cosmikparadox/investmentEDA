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
- [x] CC: `db/schema.sql` with all objects from DESIGN.md including `observation_log`, `split_mask`, `ingest_runs`, and the `observations_explore` / `observations_holdout` views. `db/init.py` that creates them. `db/units.md`. **`ingest_runs` added 2026-09-11; `db/units.md` written 2026-09-14.**
- [x] CC: `ingest/bronze.py` (atomic write, never overwrite) and `ingest/runs.py` (RunResult, start_run, finish_run). **Both done 2026-09-11 — `runs.py` 11 tests, `bronze.py` 9. Q4 answered: CC writes it, owner migrates onto it.**
- [x] CC: `core/clock.py` — every timestamp in the database is UTC, from one function. **Q3 answered 2026-09-11; convention documented at the top of `db/schema.sql`, 6 tests.**
- [x] CC: `parse_version` on `observations` and in its primary key, two-stage `observations_latest`, `parse_corrections` table, `db/migrations.py`. **Q1 answered 2026-09-11; 10 tests in `tests/test_views.py`.**
- [x] ~~**Owner:**~~ **CC, owner's call 2026-09-12:** moved `ingest/fred.py` onto `core/`, `ingest/runs.py` and `ingest/bronze.py` — `core.http.get` instead of `httpx.get`, `core.errors` instead of `BadPayload`, `core.config.api_key` instead of reading `os.environ`, `ingest.bronze.write_bronze`/`read_bronze` instead of its own pair, `core.clock.utc_now()` instead of `datetime.now()`, and `start_run()`/`finish_run()` around the whole thing so every run is recorded. **Done: 16 original tests still pass, 8 added — one row per run, a failure recorded not raised, a bronze file surviving a bad payload, and the Q1 correction end to end.**
- [x] CC: cutover recorded in `docs/DECISIONS.md` — `run_id` 1, `started_at` 2026-09-12 10:03:44 UTC. Everything in `observations` before it is BST (UTC+1).
- [x] ~~**Owner:**~~ **CC 2026-09-12:** the Q1 half — `run(conn, bronze_path=...)` skips the fetch, re-parses at the next `parse_version`, keeps the file's original `received_at`, and writes a `parse_corrections` row. A reason is required when the file's rows are already stored.
- [x] CC: `db/make_split.py` — fixed seed, 25% of ISO weeks 2015–2030 marked holdout, writes `db/split_mask.csv`. Commit the CSV. It never changes again.
- [ ] Owner: migrate anything from `docs/OBSERVATIONS.md` into `observation_log` by hand once the table exists.
- [x] CC: `db/seed_entities.sql` with the three v0 entities and their aliases.
- [x] ~~**Owner writes** `ingest/fred.py` by hand~~ **CC wrote it, owner's call 2026-09-05.** See DECISIONS. The learning goal moves to the walkthrough and to Week 4's "explain every table and column without looking", which is unchanged.
- [x] CC: walk the owner through `ingest/fred.py` line by line.
- [x] Milestone: `python -m ingest.fred` puts Brent and OVX rows into `observations`. **Done 2026-09-12: 6,101 rows a run, 2015-01-01 to 2026-09-10, run twice — 12,202 rows, two vintages, 6,101 in `observations_latest`.**

## Week 2 — the other two feeds and the idempotency test

- [x] ~~Research:~~ **CC verified live 2026-09-12** — endpoint, paging and field types confirmed; `date` is a `YYYY-MM-DD` string, not epoch milliseconds as the spec said. Findings in `docs/feeds/portwatch.md`.
- [x] ~~Research:~~ **CC verified live 2026-09-12** — `WCESTUS1`, units literally `MBBL`, no publication timestamp in the reply. Findings in `docs/feeds/eia.md`.
- [x] CC: `ingest/eia.py`. **Done 2026-09-12 — 610 weeks from 2015-01-02, 17 tests.**
- [x] CC: `ingest/portwatch.py`. **Done 2026-09-12 — the full history every call, 2,806 days x 2 series = 5,612 rows a run, one `received_at`, 21 tests.**
- [x] CC: fixture payloads and idempotency tests for all three. **Done 2026-09-12: `test_idempotency.py` (FRED, 24), `test_eia.py` (17), `test_portwatch.py` (21). 120 tests in the suite.**
- [ ] Owner: run the tests. Break one on purpose. Understand why it fails.
- [x] CC: `Makefile` with `init`, `ingest`, `test`, `check`, `dashboard`, `map` targets. **Done 2026-09-14. `make ingest` runs every feed, continues past a failure and exits 1 if any failed (FR-07), tested.**
- [x] Milestone: `make ingest` twice in a row; row count in `observations` exactly doubles. **Verified 2026-09-14: three feeds, 12,324 rows a run.**

## Week 3 — see it

- [x] CC: `app/dashboard.py` — three charts, a "Last received" table, a "Note this" box under each chart, a runs panel, and a read-only Log page. **Done 2026-09-14. FR-40 to FR-44; the grep test for FR-44 is `tests/test_app_views.py`. Driven in a real browser: charts render, the holdout gaps are breaks in the line, a note saved from the page appears on the Log page.**
- [ ] Owner: verify the holdout gaps are visible in the charts. If the charts look continuous, the app is reading the wrong view.
- [ ] Owner: every day this week, look at the dashboard for ten minutes and write at least one note. Bad notes are fine. "Nothing moved" is a note.
- [x] CC: `app/export_map.py` — CSV of entities with lat/lon. **Done 2026-09-14: `make map` writes `data/export/entities.csv`, one row, the Strait of Hormuz.**
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
