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
