# Feed: portwatch_hormuz

**Provider:** IMF PortWatch (IMF + Oxford). **Upstream:** satellite AIS, modelled estimates.
**Auth:** none. **Cadence:** weekly, Tuesdays 09:00 ET, ~2-day data lag.
**Revisions:** yes, recent weeks are backfilled silently. No vintage API. Snapshot every pull.

## Endpoint
```
https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query
```
Layer metadata: same URL without `/query`, add `?f=json`.

## Identifier
`portid = 'chokepoint6'`, `portname = 'Strait of Hormuz'`. String match is case-insensitive.

## Fields (21)
`date` (epoch **milliseconds**), `year`, `month`, `day`, `portid`, `portname`,
`n_container`, `n_dry_bulk`, `n_general_cargo`, `n_roro`, `n_tanker`, `n_cargo`,
`n_total` (**the headline count**), `capacity_*` (trade-volume estimates by type),
`capacity`, `ObjectId`.

## Query
- `where=portid='chokepoint6'`, `outFields=*`, `returnGeometry=false`, `f=json`
- Page with `resultOffset` / `resultRecordCount=1000`, `orderByFields=ObjectId ASC`
- History from 2019-01-01, ~2,800 rows. Pull all, filter locally. Do not trust
  `date>=DATE '...'` until verified on a live call.

## Verify on first run
1. `maxRecordCount` from layer metadata (assumed 1000, may be 2000).
2. Field types from layer metadata.
3. One live row shows `portid='chokepoint6'`.

## Licence
IMF terms: attribution required — "Source: IMF PortWatch, https://portwatch.imf.org".
Bulk automated download of the whole site is prohibited without permission. One
chokepoint, weekly, is fine. Do not pull all 28.

## Caveats
Modelled estimates, not raw AIS. AIS spoofing and GPS jamming in the Gulf since
Feb 2026 degrade the counts. Pre-crisis baseline ~85/day; 3–6/day in late Aug 2026.

## Canonical mapping
| series_id | field | unit | entity_id |
|---|---|---|---|
| `hormuz_transits_total` | `n_total` | `vessels` | `chokepoint:hormuz` |
| `hormuz_transits_tanker` | `n_tanker` | `vessels` | `chokepoint:hormuz` |

## Verified on a live call, 2026-09-12

Checked against the layer metadata and the real endpoint while writing
`ingest/portwatch.py`. Three of the four items above are confirmed; one is
wrong.

- **`date` is NOT epoch milliseconds.** The field type is
  `esriFieldTypeDateOnly` and it comes back as a plain `"2026-09-06"` string.
  ArcGIS serves date-only fields either way depending on a server-side setting
  we do not control, so `ingest/portwatch.py` accepts both shapes and there is a
  test asserting they produce identical rows. If it ever flips, nothing breaks.
- **`maxRecordCount` is 1000**, as assumed. `exceededTransferLimit: true` comes
  back on a full request, and paging with `resultOffset` works. Ordering by
  `ObjectId ASC` rather than by date, because paging is only safe if the server
  sorts identically on every request.
- **History is 2019-01-01 to 2026-09-06, 2,806 rows** for `chokepoint6` — three
  pages. `portid='chokepoint6'` and `portname='Strait of Hormuz'` confirmed on
  live rows.
- **The collapse is real in the data.** Late August 2026 days are 2–7 vessels
  against a pre-crisis norm near 85, and the last 30 days average 4.1. Whether
  that is ships not sailing or ships not broadcasting is exactly the question
  this feed cannot answer on its own — see the caveats above.
- **Date filtering server-side was not tested**, because it is not needed: the
  whole history is three requests, and filtering locally is visible and cheap.
