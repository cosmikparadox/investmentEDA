-- queries/asof.sql — "what did we know about this series on that date?"
--
-- Run by hand, never by the app. See queries/README.md for why that matters.
--
--     uv run python -c "import duckdb; duckdb.connect('data/controlroom.duckdb').sql(open('queries/asof.sql').read()).show()"
--
-- or, in the DuckDB CLI:
--
--     .read queries/asof.sql
--
-- WHAT IT ANSWERS
--
-- Every row in `observations` carries `received_at`: the moment WE had it. A
-- source that revises a number produces a second row rather than changing the
-- first, so the table holds every version of the truth we were ever told.
--
-- This query rewinds that. Give it a date and it returns the series as it
-- looked on that date — the numbers we actually held, not the ones we hold now.
-- If a value was revised afterwards, you get the OLD one, because that is what
-- was on the screen at the time.
--
-- That is the whole point of the design. A backtest run against today's numbers
-- silently uses information that did not exist when the decision would have been
-- made, and it will look far cleverer than it was.
--
-- A NOTE ON PARSE CORRECTIONS
--
-- `parse_version` is us fixing our own misreading of a payload, not the source
-- changing its mind, so a corrected row keeps the original `received_at`. This
-- query therefore returns the corrected reading — the best answer to "what did
-- the source tell us by then". If you ever need the different question, "what
-- did we *believe* on that date", including our own mistakes, `parse_corrections`
-- records when each fix was made and you can filter on `corrected_at`.

-- ============================ SETTINGS ============================
-- Edit these two lines, then run the file.
-- (tests/test_asof.py sets its own values and runs everything below the marker
--  line, so do not delete it.)

SET VARIABLE series = 'brent_spot';
-- `asof_date`, not `asof`: ASOF is a DuckDB keyword (it has ASOF JOINs) and
-- a variable called that is a parser error.
SET VARIABLE asof_date = TIMESTAMP '2026-09-14 00:00:00';

-- ============================ QUERY ============================

WITH known_by_then AS (
    -- Rule one: nothing that arrived after the as-of moment may be looked at.
    -- This single line is what separates a point-in-time query from a lie.
    SELECT * FROM observations
    WHERE series_id = getvariable('series')
      AND received_at <= getvariable('asof_date')
),
best_parse AS (
    -- Within one vintage, the highest parse_version is our corrected reading
    -- of that payload.
    SELECT * FROM known_by_then
    QUALIFY row_number() OVER (
        PARTITION BY feed_id, series_id, entity_id, period_start, received_at
        ORDER BY parse_version DESC
    ) = 1
),
latest_vintage_then AS (
    -- Across vintages, the most recent one we held BY THAT DATE — which is not
    -- the most recent one we hold now.
    SELECT * FROM best_parse
    QUALIFY row_number() OVER (
        PARTITION BY feed_id, series_id, entity_id, period_start
        ORDER BY received_at DESC
    ) = 1
)
SELECT
    period_start,
    value,
    unit,
    received_at    AS vintage,       -- when we got the number we are showing
    parse_version,
    source_asof,                     -- when the source says it published, if it says
    feed_id,
    bronze_path                      -- the raw file this came from, if you want to look
FROM latest_vintage_then
ORDER BY period_start;
