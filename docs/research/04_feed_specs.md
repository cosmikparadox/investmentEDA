# Data-Ingestion Feed Specs — IMF PortWatch (Hormuz), US EIA API v2, FRED

## TL;DR
- **All three feeds are free, programmatically accessible, and specced to implementation level.** PortWatch is an unauthenticated ArcGIS FeatureServer (`Daily_Chokepoints_Data`, layer 0) where Hormuz is `portid='chokepoint6'`; EIA v2 needs a free `api_key` and serves `WCESTUS1` under `petroleum/sum/sndw/data/`; FRED needs a free key and serves `DCOILBRENTEU` and `OVXCLS` from `/fred/series/observations`.
- **Two feeds require careful revision handling.** EIA weekly crude stocks ARE revised and the API only returns the latest value per period (no vintages) — snapshot yourself; FRED exposes true bitemporal vintages via ALFRED `realtime_start`/`realtime_end`; PortWatch estimates are preliminary and backfilled weekly.
- **Highest-uncertainty items are on PortWatch:** exact `maxRecordCount` (1000 inferred), exact field types, and Hub CSV download hrefs could not be captured from a live endpoint. Field names, ordering, 2019-01-01 history start, and `chokepoint6` are corroborated by IMF's own tutorial and multiple independent sources.

## Key Findings
- **PortWatch endpoint verified:** `https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query`, no auth, history from 2019-01-01, 21-field schema with `n_total` as the headline count.
- **EIA v2 verified** down to route, series, 5000-row cap, Wednesday 10:30 ET schedule. Values returned as JSON strings. Weekly stocks are revised; API shows only latest.
- **FRED verified:** both series live, 120 req/min, ALFRED vintages via `realtime_*`, `.` = missing.
- **Hormuz series is live and dramatic:** 6 transits on 2026-08-30 vs ~85/day pre-crisis.

---

## FEED 1 — IMF PortWatch: Strait of Hormuz daily vessel transits

**Endpoint (VERIFIED path):**
`https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query`
- Layer metadata: same URL without `/query`, add `?f=json`.
- ArcGIS Hub page: `https://portwatch.imf.org/datasets/42132aa4e2fc4d41bdaf9a445f688931_0/about`
- Direct download (INFERRED, not verified): `https://hub.arcgis.com/api/download/v1/items/42132aa4e2fc4d41bdaf9a445f688931/csv?layers=0`

**Auth:** None.

**Hormuz identifier:** `portid = 'chokepoint6'`, `portname = 'Strait of Hormuz'`. Case-insensitive match.

**Fields (21, VERIFIED):** `date` (epoch **milliseconds**), `year`, `month`, `day`, `portid`, `portname`, `n_container`, `n_dry_bulk`, `n_general_cargo`, `n_roro`, `n_tanker`, `n_cargo`, `n_total` (**headline count**), `capacity_container`, `capacity_dry_bulk`, `capacity_general_cargo`, `capacity_roro`, `capacity_tanker`, `capacity_cargo`, `capacity`, `ObjectId`.

**Query mechanics:**
- `where=portid='chokepoint6'`; optionally `AND date>=DATE '2026-01-01'` (validate on first run).
- `f=json`, `outFields=*`, `returnGeometry=false`.
- Page with `resultOffset` + `resultRecordCount=1000`; `maxRecordCount` INFERRED 1000 (may be 2000). Order by `ObjectId ASC`.

**History:** From 2019-01-01, ~2,600–2,800 daily rows per chokepoint. Paginated.

**Cadence:** "Updated Weekly, Tuesdays 9 AM ET" (IMF methodology page). ~2-day data lag.

**Revisions:** Preliminary; backfilled on subsequent updates. No vintage mechanism. Snapshot.

**Licence:** IMF terms — attribution required ("Source: IMF PortWatch"). Bulk automated download without permission prohibited; LLM-training use prohibited. Single chokepoint, weekly, with attribution is low-risk.

**Caveats:** Modelled AIS estimates. GPS jamming and AIS spoofing during the 2026 crisis degrade reliability. Pre-crisis baseline ~85/day; 3–6/day late Aug 2026.

**Verified vs inferred:** VERIFIED — endpoint, org id, field names/order, 2019 start, chokepoint6, weekly Tuesday cadence, no auth. INFERRED — field types, exact maxRecordCount, Hub download hrefs.

**Python (BEST RECONSTRUCTION — not run live):**
```python
import requests, datetime as dt

BASE = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/"
        "services/Daily_Chokepoints_Data/FeatureServer/0/query")

def hormuz_transits():
    rows, offset = [], 0
    while True:
        params = {
            "where": "portid='chokepoint6'", "outFields": "date,n_total",
            "orderByFields": "ObjectId ASC", "returnGeometry": "false",
            "resultOffset": offset, "resultRecordCount": 1000, "f": "json",
        }
        r = requests.get(BASE, params=params, timeout=60)
        r.raise_for_status()
        feats = r.json().get("features", [])
        if not feats:
            break
        for f in feats:
            a = f["attributes"]
            d = dt.datetime.utcfromtimestamp(a["date"] / 1000).date()
            rows.append((d.isoformat(), a["n_total"]))
        if len(feats) < 1000:
            break
        offset += 1000
    return rows
```

**Canonical:** `hormuz_transits_total` / `vessels`.

---

## FEED 2 — US EIA API v2: weekly US crude stocks excluding SPR

**Endpoint:** `https://api.eia.gov/v2/petroleum/sum/sndw/data/`
Alternative: `https://api.eia.gov/v2/seriesid/PET.WCESTUS1.W`

**Auth:** Free key from eia.gov/opendata, `api_key` param. HTTP 403 `API_KEY_MISSING` without.

**Series:** `facets[series][]=WCESTUS1`. Units: thousand barrels. `frequency=weekly`. "U.S. Ending Stocks excluding SPR of Crude Oil."

**Parameters:** `frequency=weekly`, `data[0]=value`, `facets[series][]=WCESTUS1`, `sort[0][column]=period&sort[0][direction]=asc`, `start`/`end`, `offset`/`length=5000`.

**Response:** `response.data[]` with `period`, `value` (**string — cast to float**), `units`, `series-description`. `response.warnings` if cap hit.

**Limits:** 5000 rows/request. Throttled per second and per hour, numbers unpublished; key auto-suspended briefly. Use backoff.

**Cadence:** WPSR, Wednesdays 10:30 ET (holiday shifts).

**Revisions:** **Yes.** Prior weeks revised. **API returns only latest value per period — no vintages.** Snapshot over time.

**Licence:** US government, public domain. Cite.

**Python:**
```python
import requests

API_KEY = "YOUR_EIA_KEY"
URL = "https://api.eia.gov/v2/petroleum/sum/sndw/data/"

def crude_stocks_ex_spr(start="2024-01-01"):
    params = {
        "api_key": API_KEY, "frequency": "weekly", "data[0]": "value",
        "facets[series][]": "WCESTUS1",
        "sort[0][column]": "period", "sort[0][direction]": "asc",
        "offset": 0, "length": 5000, "start": start,
    }
    r = requests.get(URL, params=params, timeout=60)
    r.raise_for_status()
    return [(row["period"], float(row["value"]))
            for row in r.json()["response"]["data"]]
```

**Canonical:** `us_crude_stocks_ex_spr` / `kbbl`.

---

## FEED 3 — FRED: Brent spot & CBOE crude oil volatility index

**Endpoint:** `https://api.stlouisfed.org/fred/series/observations`

**Auth:** Free key from fredaccount.stlouisfed.org, `api_key` param. 120 req/min with key.

**Series:**
- `DCOILBRENTEU` — Brent spot, daily, USD/bbl. Source EIA. Public domain.
- `OVXCLS` — CBOE Crude Oil ETF Volatility Index, daily. CBOE copyright — citation required. **Live via API as of 2026-09.**

**Parameters:** `series_id`, `api_key`, `file_type=json`, `observation_start`/`observation_end`, **`realtime_start`/`realtime_end`** (ALFRED vintages; closed interval; default today). For "as of date D": both = D. Full history: `realtime_start=1776-07-04&realtime_end=9999-12-31`.

**Response:** `observations[]` with `realtime_start`, `realtime_end`, `date`, `value`. **Missing = `"."`** — coerce to null.

**Limits:** `limit` up to 100000 (INFERRED). 120 req/min; HTTP 429 on breach.

**Revisions:** Rare. Use ALFRED anyway.

**Licence:** DCOILBRENTEU public domain. OVXCLS copyrighted — use, don't redistribute.

**Python:**
```python
import requests

FRED_KEY = "YOUR_FRED_KEY"
URL = "https://api.stlouisfed.org/fred/series/observations"

def fred_series(series_id, start="2019-01-01",
                realtime_start=None, realtime_end=None):
    params = {"series_id": series_id, "api_key": FRED_KEY,
              "file_type": "json", "observation_start": start}
    if realtime_start: params["realtime_start"] = realtime_start
    if realtime_end: params["realtime_end"] = realtime_end
    r = requests.get(URL, params=params, timeout=60)
    r.raise_for_status()
    return [(o["date"], None if o["value"] == "." else float(o["value"]),
             o["realtime_start"], o["realtime_end"])
            for o in r.json()["observations"]]
```

**Canonical:** `brent_spot` / `usd_per_bbl`; `ovx` / `index`.

---

## Cross-cutting 2025–2026 changes
- **EIA:** APIv1 deprecated; legacy IDs via `/v2/seriesid/{id}`. Values as strings since Jan 2024. Version 2.1.12 (March 2026).
- **FRED:** Key required for 120/min tier. ALFRED semantics unchanged.
- **PortWatch:** No auth added. IMF terms now prohibit bulk automated download and LLM-training use. Hormuz layer publish lag aligned with other chokepoints as of 2026-08-04.

## Recommendations
1. **Build PortWatch first and defensively.** On first run verify: `maxRecordCount` from layer metadata; field types; a live row shows `portid='chokepoint6'`; whether `DATE '...'` predicate works, else filter locally.
2. **Model revisions explicitly.** EIA: re-pull trailing ~8 weeks every Wednesday after 10:30 ET. FRED: pull with `realtime_*`. PortWatch: re-pull trailing ~4 weeks every Tuesday after 9 AM ET.
3. **Respect licences.** IMF attribution string; single chokepoint paced pulls; keep OVXCLS internal.
4. **Schedule around releases** and handle 429 (FRED) and 403 suspension (EIA) with backoff.
5. **Long-format schema:** `(series_id, date, value, unit, valid_time, transaction_time, source)`.

## Caveats
- PortWatch live-endpoint items (maxRecordCount, field types, Hub hrefs) inferred not fetched.
- PortWatch data materially degraded during the 2026 conflict.
- EIA has no vintage API; exact rate limits unpublished.
- OVXCLS is CBOE-copyrighted; monitor availability.
- All Python snippets are reconstructions from documentation, not executed live.
