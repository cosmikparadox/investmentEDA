# The whole system, five commands. Run them from the repo root.
#
#   make init       build or update data/controlroom.duckdb
#   make ingest     pull every feed once, and store what comes back
#   make test       run the tests (no network, no API keys needed)
#   make check      lint and test — run this before every commit
#   make dashboard  open the app in a browser
#
# `uv run` puts the project's own Python and its dependencies on the path, so
# nothing has to be installed globally and nothing has to be "activated" first.

.PHONY: help init ingest test check dashboard map clean-pycache

# Running `make` on its own lists what there is, rather than doing something.
help:
	@echo "make init       build or update the database (safe to re-run)"
	@echo "make ingest     pull every feed once; exits 1 if any feed failed"
	@echo "make test       run the tests"
	@echo "make check      ruff + pytest; run before committing"
	@echo "make dashboard  open the dashboard in a browser"
	@echo "make map        write the Kepler.gl CSV of entities with coordinates"

init:
	uv run python db/init.py

# Every feed, one after another. A feed that fails does not stop the others,
# and the command exits non-zero at the end if any of them did (PRD FR-07).
ingest:
	uv run python -m ingest

test:
	uv run pytest -q

# Lint and tests together. If this is red, the commit waits.
check:
	uv run ruff check .
	uv run pytest -q

dashboard:
	uv run streamlit run app/dashboard.py

map:
	uv run python app/export_map.py
