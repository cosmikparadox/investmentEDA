# Units

The canonical unit strings. Every row in `observations` carries one of these in
its `unit` column, and nothing else is allowed (PRD DR-04).

Why a fixed list: a source's own unit string is written for a human reading a
report, not for a database. The EIA says `MBBL`, meaning thousands of barrels —
the M is the Roman thousand, not the metric million, and anyone who reads it as
millions is out by a factor of a thousand in the direction that looks plausible.
Translating every source's wording into one list at the point of ingestion means
that trap is sprung once, in one place, with a comment next to it.

| unit | means | used by |
|---|---|---|
| `usd_per_bbl` | US dollars per barrel | `brent_spot` |
| `index` | an index number with no unit — only comparable with itself | `ovx` |
| `kbbl` | thousands of barrels | `us_crude_stocks_ex_spr` |
| `vessels` | a count of ships | `hormuz_transits_total`, `hormuz_transits_tanker` |

## Adding one

A new unit needs a dated entry in `docs/DECISIONS.md` saying what it measures and
why an existing one would not do. The list is short on purpose: every extra unit
is another way for two series to look comparable when they are not.

## What a source calls them

| source says | we store | note |
|---|---|---|
| `MBBL` | `kbbl` | EIA. M is the Roman thousand. Their `series-description` spells it out as "Thousand Barrels". |
| `Dollars per Barrel` | `usd_per_bbl` | FRED, `DCOILBRENTEU`. |
| `Index` | `index` | FRED, `OVXCLS`. Computed by CBOE from WTI options. |
| (no unit given) | `vessels` | IMF PortWatch. The fields are counts: `n_total`, `n_tanker`. |
