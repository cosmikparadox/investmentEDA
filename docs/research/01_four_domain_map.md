# The 2026 Iran War & Strait of Hormuz Crisis: A Four-Domain Investing Map and Data-Sourcing Framework

*Analytical map as of 31 August 2026. Not investment advice — a distillation framework and raw material for independent quantitative analysis.*

## TL;DR

- **Tanker shipping is the single most data-rich AND retail-tradable domain of the four** — freight rates, transit counts, war-risk premia and vessel values are all published at high frequency (much of it free via IMF PortWatch, Baltic Exchange weekly roundups, straits.live), and the thesis is expressible through ordinary equities (FRO, DHT, INSW, STNG) and one purpose-built ETF (BWET). But most of the move is already priced: BWET is up roughly 1,000% YTD and the Baltic TD3C benchmark printed near $585,000/day in late August, so the edge now is in fading spikes, not chasing them.
- **The energy complex is the second most data-rich and by far the most retail-accessible; "semis-as-a-Hormuz-trade" is largely a narrative confusion** — Brent ~$88 already embeds a ~$18–20 war premium that has round-tripped from $120+ in April. Semiconductors are being driven by an AI-capex supercycle (TSMC July 2026 revenue NT$467.58bn, +44.7% YoY) that is causally independent of Hormuz; the real energy→semis transmission (neon/rare gases, power costs) is weak and, per TSMC management, currently immaterial.
- **Defence/gold is the "changing world order" adjacency with the longest runway but the least crisis-specific data** — a structural rearmament + debasement story (NATO's Hague pledge to 5% of GDP by 2035; central banks adding a record net 289 tonnes of gold in Q2 2026 per the World Gold Council) that predates and outlasts Hormuz. **Rank by data richness: (1) Tankers, (2) Energy, (3) Defence/Gold, (4) Semiconductors** — semis ranks last because there is no clean, high-frequency data series that isolates a Hormuz effect from the AI cycle.

## Key Findings

1. **Six months in, the "shock" phase is over and the "attrition" phase has begun.** The strait has swung between full closure, partial reopening, and re-closure at least three times since 28 February 2026. As of 23 August, IMF PortWatch recorded just **3 vessel transits/day** versus an **~85/day pre-crisis baseline**, yet Goldman Sachs (via Bloomberg, 28 August 2026) estimates total Gulf oil exports have recovered to **roughly two-thirds of pre-war levels (15–16 mb/d)** via dark crossings, ship-to-ship transfers, and bypass pipelines, with ~6–8 mb/d still crossing Hormuz itself. This reconciliation — very few *counted transits* but substantial *oil still flowing* — is the crux of why Brent is $88 and not $130.

2. **The gap between narrative and pricing is now the trade.** Headlines say "closed"; the physical market says "two-thirds recovered." Brent at ~$88 (vs $69.85 the day before the war) implies a war premium of roughly $18–20/bbl. Per the EIA's August 2026 STEO, Brent is forecast to average ~$85 in 3Q26 and ~$87 for full-year 2026 (easing to ~$69 in 2027), and the agency does not expect Middle East production to return to near pre-conflict levels until early 2027, with ~0.6 mb/d of residual disruption persisting through end-2027.

3. **War-risk insurance, not physical blockage, is the binding constraint.** Additional war-risk premiums have gone from ~0.25% of hull value pre-war to **7.5–10% currently** (Marsh via S&P Global Platts, 22 July 2026) — a $100M VLCC now faces $7.5–10M per transit. During the 1980s Tanker War, only 1–2% of merchant traffic was ever attacked and oil kept flowing; the difference in 2026 is that insurers withdrew cover, which halted traffic more effectively than mines.

4. **Volatility is oil-specific, not systemic.** OVX was ~47 on 18 August, down from a wartime peak of ~126 in early March but well above its ~20s calm-market range; VIX was ~16, near normal. The market is treating this as a contained energy/shipping event, not a global risk-off episode.

## Domain 1 — Tanker Shipping & Freight

### (a) Current state / what's priced in
The Baltic Exchange TD3C (VLCC Middle East Gulf–China) went from ~$29,000/day in early January to a record $423,736/day at war outbreak, spiked to $601,569/day in mid-March, and was reported near $585,000/day in late August. **Critical caveat:** Lloyd's List, Clarksons and BRS all describe the MEG TD3C as effectively "imaginary" — because the Ras Tanura→Ningbo route is commercially inaccessible, Baltic panellists derive it from Yanbu (Red Sea) proxy fixtures plus an estimated risk premium, not cleared trades through Hormuz, and it is a 15–30-day-forward assessment. Atlantic-basin VLCC indices (TD15, TD22) are based on real fixtures and sit roughly $300,000/day *below* the MEG indices. BWET is up ~1,000% YTD. Frontline (FRO) roughly doubled YoY. Most of the move is done; you are now trading mean-reversion risk.

### (b) Data sources — RICHEST OF THE FOUR
- **IMF PortWatch** (portwatch.imf.org): daily chokepoint transit counts + trade-volume estimates for 28 chokepoints and 2,065 ports; updated weekly Tuesdays 9am ET; **free**; full API (ArcGIS), CSV/GeoJSON download. This is the series prediction-market reopening contracts resolve on.
- **Baltic Exchange**: TD3C, TD15, TD22, dirty/clean tanker indices, FFA settlement. **Free** weekly "Tanker report" roundup; real-time/full data is paid.
- **straits.live**: purpose-built crisis tracker; **free** JSON API; bundles PortWatch transits, Brent/WTI, insurance multiples, carrier suspensions.
- **Lloyd's List Intelligence**: gold-standard maritime journalism + AIS; **paid** (institutional).
- **AIS/vessel tracking**: MarineTraffic, VesselFinder (freemium, ~$10–50/mo); Spire, Kpler, Vortexa (institutional). Note: GPS jamming, AIS spoofing and vessels "going dark" are heavily degrading AIS reliability in the Gulf.
- **The Signal Group / Breakwave Advisors / Clarksons**: weekly tanker monitors, some free.

### (c) Tradeable instruments
- **Retail:** FRO, DHT, INSW, STNG/ASC, NAT, OET; ETFs **BWET** (pure freight-futures; 3.50% expense cap; monthly roll — structural decay risk) and **BOAT** (global shipping; 0.69% fee; 51 operators).
- **Futures/CFD:** listed FFAs via brokers with derivatives access.
- **Institutional-only:** OTC FFAs, physical vessels, period charters.

### (d) State variables / leading indicators
Leading: war-risk AP (% hull), JWC listed-area designations, PortWatch transit count, carrier-suspension announcements, insurer cancellation notices. Lagging: TD3C print, vessel resale values, tanker-company earnings.

### (e) Scenarios / base rates
- **1980s Tanker War (1984–88):** ~451 ships attacked over 8 years, but oil kept flowing; only 1–2% of Hormuz traffic attacked. Lesson: physical resilience is high; the 2026 difference is insurance withdrawal.
- **2019 Gulf tanker attacks:** brief spikes, fast normalization.
- **2024 Red Sea/Houthi:** Suez transits fell ~70%; disruption persisted 18+ months.
- **Ever Given (2021):** 6-day blockage, flows normalized within weeks.
- **Suez 1967 closure:** lasted 8 years — the tail-risk analog for "frozen conflict."

### (f) What makes this trade fail
BWET's structural decay and single-event dependency mean a ceasefire headline can erase months of gains in days (TD3C fell 20% in a single session in December). Retail typically buys the ETF *after* the spike, holds through mean-reversion, and eats contango. The "imaginary" MEG index means paper gains may not reflect realizable cash.

## Domain 2 — Energy Complex (Crude, Refining, Gas/LNG)

### (a) Current state / what's priced in
Brent ~$88, having round-tripped from a dated-Brent record $144.42 in early April back below $70 in late June and back up on August re-escalation. The war premium is real but modest because OPEC+ had ~5–6 mb/d spare capacity and the IEA executed its largest-ever coordinated reserve release. **Natural gas/LNG is where the tail is fatter and less priced:** ~20% of global LNG transits Hormuz (Qatar has no alternative route); TTF rose above €69/MWh and JKM spiked to ~$22/MMBtu. Europe entered winter with storage only **~63% full** (lowest seasonal since 2009).

### (b) Data sources — SECOND RICHEST, MOST ACCESSIBLE
- **EIA**: STEO (monthly), Weekly Petroleum Status Report (Wed), Natural Gas Storage (Thu). All **free**, API.
- **IEA**: Oil Market Report, Gas Market Report. Free summaries; full reports paid.
- **OPEC MOMR:** **free** PDF, monthly.
- **FRED**: Brent/WTI, OVXCLS, TTF, gasoline — **free**, API, daily.
- **Kpler / Vortexa / Energy Aspects:** institutional/paid.

### (c) Tradeable instruments
- **Retail:** USO/BNO (contango drag), UNG (severe decay), XLE/XOP/VDE, majors (XOM, CVX, SHEL), refiners (VLO, MPC, PSX), LNG names.
- **Futures/CFD:** CL, BZ, NG, TTF, JKM.
- **Institutional:** physical cargoes, OTC swaps.

### (d) State variables / leading indicators
Leading: PortWatch transits, bypass-pipeline utilization, OPEC+ spare capacity, SPR/IEA actions, JWC designations, Qatar force-majeure status. Lagging: EIA weekly inventories, refinery margins. Term structure is itself a leading signal.

### (e) Scenarios / base rates
- **Negotiated reopening:** even after a signed deal, normalization takes weeks to months (mine clearance; idled fields restart). EIA assumes ~0.6 mb/d disruption persists through end-2027.
- **Bypass math:** realistic total bypass capacity 2.6–5.5 mb/d = only **13–28% of normal ~20 mb/d Hormuz flow. LNG bypass capacity: zero.**
- **1990 Gulf War:** Brent spiked then fell within months.
- **2022 Ukraine/gas:** TTF peaked €345/MWh.

### (f) What makes this trade fail
Oil-ETF contango/roll decay. The dominant failure mode: OPEC+ spare capacity + dark flows + bypass keep the physical market adequate, so the war premium bleeds out while you wait.

## Domain 3 — Semiconductor Supply Chain

### (a) Current state — SEPARATING SIGNAL FROM NARRATIVE
**"Semis as a Hormuz trade" is largely a narrative confusion.** The semiconductor tape in 2026 is driven by an AI-capex supercycle: TSMC Q1 revenue +40.6% YoY, June best month ever, July NT$467.58bn (+44.7% YoY). It raised full-year guidance to >40% growth. On its Q1 call, TSMC management explicitly said it "does not expect any near-term impact" from Middle East disruptions.

**The real (weak) transmission channels:** energy input costs (modest); neon/rare gases (a Russia/Ukraine chokepoint, not Hormuz); demand destruction (second-order); shipping (chips fly by air).

### (b) Data sources — LEAST CRISIS-RELEVANT (ranked 4th)
- **TSMC monthly revenue**: monthly, ~10th, **free**.
- **WSTS Blue Book**: monthly, **free**, ~6-week lag.
- **SEMI**: mostly **paid**.
- **SIA**: **free** press releases.
- **Rare-gas prices:** no clean free feed.

### (c) Tradeable instruments
SOXX/SMH, NVDA, TSM, AMD, ASML, AVGO, MU. No instrument isolates a "Hormuz semiconductor" exposure.

### (d)–(f)
Leading indicators track the AI cycle, not Hormuz. 2022 neon precedent: prices tripled, no material chip shortage. Failure mode: buying semis "because of Hormuz" when the driver is AI capex — mismatched thesis and instrument.

## Domain 4 — Defence, Middle-Power Industrials & Gold/Monetary-Order

### (a) Current state
**Defence:** NATO Hague Summit committed 32 members to 5% of GDP by 2035. Europe and Canada invested $574bn in 2025, +20% real. Rheinmetall up >1,000% above pre-Ukraine levels, though it derated ~38% from its January 2026 peak on a revenue miss; record order backlog €63.8bn. **Gold:** hit ~$5,600/oz early 2026, then corrected 10%+; central banks added net 289 tonnes in Q2 2026, strongest Q2 on record, *into* falling prices. A record 45% of central banks plan to add more.

### (b) Data sources — MODERATE (ranked 3rd)
- **World Gold Council**: quarterly, **free**.
- **LBMA / Kitco / COMEX / FRED**: daily, **free**.
- **CFTC COT**: weekly, **free**.
- **SIPRI**: annual, **free**.

### (c) Tradeable instruments
ITA/PPA/XAR, European defence ETFs, Rheinmetall, BAE, Saab, Leonardo, Hanwha; GLD/IAU/GLDM, GDX/GDXJ.

### (d)–(f)
Leading: budget announcements, order backlogs, central-bank purchases, real yields. Failure: valuations already embed years of growth; gold fell 10% despite the war. Neither is a clean Hormuz trade.

## Diplomacy & Normalization Timeline
Iran and Oman reached an understanding on a temporary joint maritime corridor (reported 27–28 August), but Iran insists this "does not mean the Strait is reopened." Iran's conditions: US must lift naval blockade, return to June ceasefire terms, unfreeze funds, halt Israeli strikes on Lebanon. Repeated cycles of "deal close" → attack → re-escalation since March. Physical normalization after any signed deal: mine clearance weeks–months; EIA sees production near pre-conflict only by early 2027.

## Second- & Third-Order Effects
- **Insurance:** JWC redesignated the whole Arabian Gulf a conflict zone; P&I clubs issued cancellation notices; Hapag-Lloyd war-risk surcharge up to $3,500/container.
- **Rerouting infra:** Fujairah, Khor Fakhan, Sohar as trans-shipment hubs; Petroline (Yanbu-capped ~3 mb/d); ADCOP (1.8 mb/d); UAE West-East line to ~3.6 mb/d by 2027.
- **Asian refiners:** India, China, Japan, South Korea take ~84% of Hormuz crude.
- **European gas:** storage ~63%, TTF asymmetric upside into winter.
- **Gulf fiscal:** Saudi breakeven ~$90–95 (Bloomberg Economics) vs ~$80–85 (IMF/Oxford). Bahrain stressed ($110+).

## Recommendations (framework, not advice)

**Stage 1 — Build the free data spine first.** PortWatch, straits.live, EIA, FRED, Baltic weekly, WGC + CFTC COT, TSMC monthly.

**Stage 2 — Pick the domain matched to your account and edge.** Ordinary brokerage: energy equities/refiners and defence/gold ETFs. Avoid "semis as a Hormuz trade."

**Stage 3 — Trade the narrative-vs-pricing gap, not the headline.** European gas is the least-priced asymmetric tail.

**Benchmarks that would change the stance:**
- PortWatch transits sustainably >40/day → reopening underway.
- War-risk AP below ~2% of hull → insurers re-entering.
- Brent breaking $100 on a *confirmed* new physical outage → escalation regime.
- OVX back to ~25 → crisis premium gone.
- EU gas storage failing to reach ~80% by 1 Nov → gas squeeze confirmed.

## Comparative Ranking

| Domain | Data availability | Retail tradability | How much priced in | Edge for non-institutional |
|---|---|---|---|---|
| **Tankers/Freight** | 5/5 | 4/5 | Mostly priced | Low–moderate, fade-only |
| **Energy** | 4/5 | 5/5 | Crude priced; gas less so | Moderate — European gas tail |
| **Defence/Gold** | 3/5 | 5/5 | Substantially (structural) | Moderate, not a Hormuz edge |
| **Semiconductors** | 2/5 | 4/5 | AI-cycle priced | Lowest — thesis mismatch |

## Caveats
- Forward-looking figures are forecasts. The strait has reversed direction 3+ times.
- The TD3C is "imaginary" — a panel assessment, not cleared trades.
- AIS is degraded — transit counts understate real oil movement.
- Source quality: IMF, EIA, IEA, Lloyd's List, S&P Global, Bloomberg, NATO, WGC are primary; crisis-tracker sites and trade blogs are secondary — corroborate before acting.
- This is a framework, not a recommendation.
