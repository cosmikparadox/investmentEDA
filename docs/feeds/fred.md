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
- **`realtime_start` is not today's date.** It comes back equal to
  `realtime_end` when the vintage parameters are not passed, i.e. "this is one
  snapshot, the current one" — but the date is the day *that series* was last
  refreshed. Confirmed on 2026-09-04: `OVXCLS` returned `2026-09-04`,
  `DCOILBRENTEU` returned `2026-09-02`, in calls seconds apart. The
  `fred/series` endpoint agrees: Brent's `last_updated` is `2026-09-02`.
  (Watch out when checking this by hand — FRED's responses are cached, and an
  early call of ours came back with today's date for both before settling
  down.)

  **Where each date goes in `observations`, because this is a trap:**

  | column | value | why |
  |---|---|---|
  | `received_at` | our own clock at fetch time | It is *our* vintage — when we had it. It is part of the primary key, which is what makes a re-run append instead of collide. |
  | `source_asof` | FRED's `realtime_start` | DESIGN.md: "when the SOURCE says it published, if known". Exactly this. |

  Putting FRED's `realtime_start` into `received_at` looks careful and breaks
  the design. Brent's stays `2026-09-02` until FRED next refreshes it, so every
  daily run would write an identical primary key, `INSERT OR IGNORE` would
  silently drop the rows, and the record of "we checked on these days and it
  had not changed" would be lost. The Week 2 idempotency test — run twice, row
  count doubles — would fail. Two columns exist precisely so neither date has
  to stand in for the other.
