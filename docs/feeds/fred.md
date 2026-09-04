# Feed: fred_brent_ovx

**Provider:** FRED, St. Louis Fed. **Upstream:** EIA (Brent), CBOE (OVX).
**Auth:** free key, `api_key` param. 120 requests/min with key; HTTP 429 on breach.
**Cadence:** daily, business days.
**Revisions:** rare. But FRED has **native vintages** via ALFRED — use them anyway.

## Endpoint
```
https://api.stlouisfed.org/fred/series/observations
```

## Series
| series_id (FRED) | what | unit | licence |
|---|---|---|---|
| `DCOILBRENTEU` | Brent spot, Europe | USD/bbl | public domain |
| `OVXCLS` | CBOE crude oil volatility index | index | CBOE copyright — use, don't republish |

## Parameters
```
series_id=...   api_key=...   file_type=json
observation_start=YYYY-MM-DD   observation_end=YYYY-MM-DD
realtime_start=YYYY-MM-DD   realtime_end=YYYY-MM-DD   <- vintage window
```
For "as it looked on date D": `realtime_start=D&realtime_end=D`.
For full revision history: `realtime_start=1776-07-04&realtime_end=9999-12-31`.

## Response
`observations[]` with `date`, `value`, `realtime_start`, `realtime_end`.
**Missing values are the string `"."`** — coerce to NULL.

## Canonical mapping
| series_id | FRED | unit | entity_id |
|---|---|---|---|
| `brent_spot` | `DCOILBRENTEU` | `usd_per_bbl` | `benchmark:brent` |
| `ovx` | `OVXCLS` | `index` | `benchmark:brent` |

## Verified on a live call, 2026-09-04
Key works, both series return HTTP 200 with the documented shape.

- **The two series do not end on the same day.** `OVXCLS` was current to
  2026-09-03; `DCOILBRENTEU` only to 2026-09-01. Brent runs two or three
  business days behind. An ingestor that assumes both series cover the same
  date range will be wrong most days. Ask for a window and store whatever
  comes back.
- **The `"."` missing-value marker is real and common.** 174 rows of
  `DCOILBRENTEU` for 2026 to date, 6 of them `"."` — New Year's Day, Good
  Friday, the early-May and late-August UK bank holidays. Note that
  2026-08-31 is `"."` for Brent but has a real value for OVX: London was
  shut, Chicago was not. Store these as `NULL` in `value`, do not skip the
  row. A published gap is information.
- `realtime_start`/`realtime_end` both come back as today's date when the
  vintage parameters are not passed, i.e. "this is what the series looks like
  right now".
