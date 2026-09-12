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

## Verified on a live call, 2026-09-12

Endpoint, parameters and response shape are exactly as documented above.
`units` really is the literal string `"MBBL"`. Confirmed while writing
`ingest/eia.py`.

- **610 weeks** returned for `start=2015-01-01`, from 2015-01-02 to 2026-09-04,
  well inside the 5000-row cap — one page. The ingestor pages anyway, and
  refuses to store a run where `len(rows) < response.total`, because a silently
  truncated series looks exactly like a series that ends.
- **`response.total` is the row count for the whole query**, not for the page.
  That is what makes the truncation check possible.
- **There is no publication timestamp anywhere in the reply.** The release
  schedule is Wednesday 10:30 ET, but a schedule is not a timestamp, so
  `source_asof` is stored as NULL rather than a guess. `received_at` is the only
  honest time axis this feed has.
- **The period is a week-ending Friday** — 2026-07-03, 2026-07-10 and so on.
  Stored with `period_start = period_end = that Friday`, because ending stocks
  is a level in the tanks on that day, not a flow across the week.
- **No revision has been observed yet.** Both pulls so far agree. That is
  expected: revisions show up over weeks, which is the point of running this
  daily and keeping every vintage.
