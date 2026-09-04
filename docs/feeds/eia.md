# Feed: eia_crude_stocks

**Provider:** US EIA, API v2. **Upstream:** EIA weekly survey.
**Auth:** free key from eia.gov/opendata, `api_key` query param. 403 without it.
**Cadence:** weekly, Wednesdays 10:30 ET (holiday shifts). Describes prior week.
**Revisions:** yes. Prior weeks are revised in later releases. **The API returns
only the latest value per period — no vintages.** Re-pull trailing 8 weeks every
Wednesday. This feed is why the bitemporal design exists.

## Endpoint
```
https://api.eia.gov/v2/petroleum/sum/sndw/data/
```
Alternative by legacy ID: `https://api.eia.gov/v2/seriesid/PET.WCESTUS1.W`

## Parameters
```
frequency=weekly
data[0]=value
facets[series][]=WCESTUS1
sort[0][column]=period&sort[0][direction]=asc
start=YYYY-MM-DD   end=YYYY-MM-DD
offset=0   length=5000
```

## Response
`response.data[]` with `period`, `value` (**a string — cast to float**), `units`
(the literal string is **`"MBBL"`**, not "thousand barrels" — M is the Roman
thousand, so MBBL means thousand barrels; `series-description` spells it out as
"Thousand Barrels"), `series-description`. `response.warnings` present if the
5000-row cap was hit.

## Limits
5000 rows/request. Throttled per second and per hour, numbers unpublished; key
is auto-suspended briefly on breach. Use backoff.

## Licence
US government work, public domain. Cite EIA.

## Canonical mapping
| series_id | unit | entity_id |
|---|---|---|
| `us_crude_stocks_ex_spr` | `kbbl` | `country:USA` |
