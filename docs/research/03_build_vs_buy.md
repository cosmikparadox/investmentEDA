# Build vs Buy: A Practical Guide to a Commodity & Supply-Chain "Control Room" and Agent-Based Trade Research Platform (UK Retail, 2026)

## TL;DR
- **Buy the data, rent the terminal, build only the thin overlay on top.** The professional "control room" (Bloomberg ~$31,980/seat/yr; Kpler/Vortexa/Wood Mackenzie quote-only enterprise) is out of reach and mostly unnecessary. A beginner can assemble genuine cross-vertical coverage almost entirely from FREE government/institutional APIs (IMF PortWatch, EIA, GIE AGSI+, USDA NASS, GDELT, FRED, GPR index) and visualise it in Grafana or Streamlit + Kepler.gl.
- **Build the monitoring/intelligence system first; do NOT build an automated trading bot.** LLM agents are good at research synthesis, monitoring, alerting and unstructured extraction, and bad at alpha generation and execution. Roughly 70% of UK CFD accounts lose money; fewer than 1% of day traders are reliably profitable. The credible edge for an individual is slow, discretionary, long-horizon macro decisions.
- **Realistic path: ~£0–20/month for a serious hobbyist stack, scaling to £100–500/month only when you know what you're missing.** In the UK, prefer Interactive Brokers for programmatic futures access; spread betting is CGT-free while retail CFDs are leverage-capped.

## Key Findings

**1. The institutional control room is priced for firms.** Bloomberg ~$31,980/seat/yr single, ~$28,320 multi-seat, two-year commitment. Kpler (now owns MarineTraffic, FleetMon, Spire Maritime), Vortexa, Wood Mackenzie, S&P Platts, ICIS, Argus, Windward, Sayari, Interos, Everstream, Altana, Panjiva — all enterprise, no individual tier.

**2. Prosumer tools give most of the feel cheaply.** TradingView, Koyfin (Free; Plus ~$39/mo; Pro ~$79/mo). Programmatic: Databento (~$179/mo live CME), Polygon (~$199/mo futures). EODHD, FMP, Alpha Vantage, Twelve Data cheaper but shallow on commodities.

**3. Free feeds give genuine coverage.** PortWatch (free API, weekly Tue 9am ET), EIA (free API), GIE AGSI+ (free API), USDA NASS (free API), FRED, UN Comtrade, GDELT (free, 15-minute global news). Unavoidable paid gaps: real-time intraday futures, vessel-level AIS, proprietary oil-flow estimates.

**4. The build stack is mature and free.** Python + pandas + DuckDB/Postgres, Prefect/Dagster, Grafana or Streamlit, Kepler.gl for the map.

**5. LLM trading agents are promising in papers, unproven in the wild.** TradingAgents, FinMem, FinAgent, FinCon report strong backtests; reviewers call them "too optimistic to be true"; 2025-26 critical papers (TradeTrap) question reliability.

## PART 1 — What already exists

### (a) Institutional platforms

| Platform | Covers | Map | API | Cost |
|---|---|---|---|---|
| Bloomberg Terminal | All asset classes | Yes | Limited | ~$31,980/seat |
| LSEG Workspace | Cross-asset, oil flows | Some | Yes | ~$12–22k est. |
| S&P Platts / ICIS / Argus | Commodity pricing | Some | Yes | Enterprise |
| Wood Mackenzie | Upstream energy, metals | Yes | Yes | Enterprise |
| Kpler | Commodity/maritime flows | Yes | Yes | Enterprise |
| Vortexa | Oil & gas cargo tracking | Yes | Yes | Enterprise |
| Windward / Spire | Maritime AI / satellite AIS | Yes | Yes | Enterprise |
| MarineTraffic | AIS, port calls | Yes | Yes | ~$100/mo API entry |
| Sayari / Interos / Everstream / Resilinc / project44 / Altana | Supply-chain risk & networks | Various | Yes | Enterprise |
| ImportGenius | Customs/bill-of-lading | No | Yes | ~$125–199/mo |
| Panjiva / Datamyne | Customs records | No | Yes | Enterprise |

Individual-accessible: MarineTraffic and ImportGenius. Everything else enterprise.

### (b) Prosumer tools

| Tool | Pricing | Commodity/shipping | API |
|---|---|---|---|
| TradingView | Free; ~$15–60/mo | Futures charts, Pine alerts | Limited |
| Koyfin | Free; $39–79/mo | Commodities, macro dashboards | Limited |
| Databento | Pay-as-you-go; ~$179/mo live CME | CME/ICE/EEX | Excellent |
| Polygon | ~$199/mo futures | CME group | Good |
| Alpha Vantage / Twelve Data / EODHD / FMP | Free to ~$100/mo | Shallow on commodities | Easy |
| Barchart OnDemand | Usage-based | Ag/commodity strong | Good |

### (c) Open-source stacks
**Kepler.gl** is the standout for a live layered map: deck.gl/MapLibre, millions of points in-browser, time playback, near-no-code. **Grafana** best for live time-series and alerting, no native geospatial. **Streamlit** / **Dash** for custom Python apps in days. Realistic: static map with overlays in a weekend; live multi-layer dashboard in a month or two; polished control room in a quarter-plus.

### (d) Consumer products doing all three
None. Closest free tool is IMF PortWatch. This gap is why a thin personal overlay is worthwhile.

## PART 2 — The data layer

**Maritime/AIS:** IMF PortWatch (free API); MarineTraffic (~$100/mo API); VesselFinder (credit-based); Datalastic (from €99/mo); Spire (enterprise); AISHub (free with contribution); aisstream.io (free WebSocket); Global Fishing Watch (free). Caveat: spoofing/dark fleet means AIS is incomplete where interest is highest.

**Energy:** EIA (free API v2); GIE AGSI+ (free API); ENTSOG (free); OPEC MOMR (free PDF); IEA (mostly paid); Genscape/Refinitiv (enterprise).

**Agriculture:** USDA NASS Quick Stats (free API); USDA FAS PSD/GAIN (free); WASDE (free); CONAB (free); NOAA/NASA/Copernicus satellite (free); Descartes Labs (enterprise); CFTC COT (free). **Gro Intelligence shut down June 2024** — cautionary tale about single-vendor dependence.

**Semiconductors:** TSMC monthly revenue (free); Taiwan MOF exports (free); Korea 20-day exports (free); SEMI/WSTS/SIA (mostly paid); ASML bookings; hyperscaler capex.

**Cross-cutting:** FRED, World Bank, UN Comtrade, Eurostat, CFTC COT, CME/ICE, Caldara-Iacoviello GPR (free, CC-BY, matteoiacoviello.com), Baltic Exchange (paid), GDELT (free), NewsAPI (freemium), RavenPack (enterprise).

**FREE combination with real coverage:** PortWatch + aisstream + EIA + AGSI+ + ENTSOG + OPEC + USDA NASS + WASDE + NOAA + CFTC COT + TSMC + FRED + GDELT + GPR. **Paid gaps:** intraday futures (~$179/mo), vessel-level AIS (~€99–100/mo), proprietary oil flows (unavailable).

## PART 3 — The build path

### (a) Staged roadmap
- **Weekend:** Python environment, pull one API, plot in Jupyter, one dataset on Kepler.gl.
- **First month:** pandas + APIs; 3–4 feeds into DuckDB; schedule with Prefect; first Streamlit/Grafana dashboard.
- **First quarter:** map overlay, Docker, GDELT monitoring + alerting; simple backtest in VectorBT.
- **First year:** working control room, alerting, research log, paper-trading connection via IBKR only if warranted.

Tech: **DuckDB** (upgrade to Postgres/Timescale only when needed); **Prefect or Dagster**; **Grafana** for live time-series, **Streamlit** for custom apps, **Kepler.gl** for maps.

### (b) Skills and learning
Python for Everybody (free); fast.ai; "Python for Data Analysis" (McKinney); QuantEcon (free); Ernie Chan "Quantitative Trading"; López de Prado "Advances in Financial Machine Learning"; Hull "Options, Futures and Other Derivatives"; Kaggle. 3–6 months part-time to be productive.

### (c) Backtesting frameworks

| Framework | Learning curve | Cost | Futures | Live |
|---|---|---|---|---|
| QuantConnect/LEAN | Steep | Free tier | Yes | Yes (same code) |
| Backtrader | Moderate | Free | Yes | Limited |
| VectorBT | Moderate | Open + PRO | Yes | No |
| Zipline-Reloaded | Moderate | Free | Equity-focused | Limited |
| Nautilus Trader | Steep | Free | Yes | Yes |
| bt | Easy | Free | Portfolio-level | No |

Recommendation: VectorBT to triage, QuantConnect/LEAN if going live, Nautilus if execution realism matters. Pitfalls: lookahead bias, survivorship bias, overfitting/p-hacking, ignoring costs and slippage. Vectorised backtests "lie about microstructure."

### (d) UK-accessible brokers

| Broker | API | Futures/options | Notes |
|---|---|---|---|
| Interactive Brokers (UK) | TWS API, ib_insync | Yes — real exchange | FCA-regulated; best route for futures; 57.9% of retail CFD accounts lose money |
| Alpaca | REST | US-focused | Check UK eligibility |
| Trading 212 | None official | No | CFD/invest only |
| Saxo Bank | OpenAPI | Yes | Good API |
| IG Group | REST/streaming | Spread betting + CFD | Strong for spread betting |
| Tradovate / AMP | Rithmic/CQG | Yes (US futures) | Futures-specialist |

FCA retail rules: CFD leverage caps 30:1 (major FX), 20:1 (gold, major indices), 10:1 (other commodities), 5:1 (equities); negative-balance protection; crypto CFDs banned; brokers must publish loss percentages. Exchange futures via IBKR/Saxo not subject to CFD caps but need appropriateness assessment. FSCS covers eligible IBKR UK assets to £85,000.

### (e) LLM-driven trade research — honest state
Credible: TradingAgents, FinMem, FinAgent, FinCon, QuantAgent report improved backtests. But: reviewers call numbers "too optimistic to be true"; TradeTrap/FinPos show agents solve a "simplified financial game"; none has a public, replicated, costs-included live track record. **Agents do well:** synthesis, monitoring, alerting, extraction, data gathering. **Badly:** alpha generation, prediction, autonomous execution. Beware "AI trading bot" marketing.

## PART 4 — Realism, cost and risk

### (a) Cost tiers
- **Free/hobbyist (£0–20/mo):** all free APIs, Kepler/Grafana/Streamlit, local DuckDB. Real cross-vertical monitoring and a map.
- **Serious (£100–500/mo):** Databento or Polygon, MarineTraffic/Datalastic, Koyfin Pro, maybe ImportGenius.
- **Semi-pro (£1,000–5,000/mo):** multiple premium APIs, cloud. Still nowhere near a Kpler or Bloomberg seat. Diminishing returns — most edge is process, not more data.

### (b) The edge question
Investors Centre April 2026 aggregate of 14 FCA brokers: **69.9% mean of retail CFD accounts lose money** (range 51%–82%). Barber, Lee, Liu & Odean (Taiwan, 1992–2006): "Less than 1% of the day trader population is able to predictably and reliably earn positive abnormal returns net of fees." Chague, De-Losso & Giovannetti (Brazil, 2020): "97% of the 1,551 individuals who persisted for more than 300 trading days lost money... no evidence of learning by day trading." The plausible individual edge: patience, long horizon, cross-domain synthesis, freedom from benchmark pressure — slow discretionary macro, not day trading.

### (c) UK regulatory and tax
Spread betting: CGT-free, stamp-duty-free, losses not offsettable. CFDs and exchange futures: CGT (18%/24% above £3,000 allowance 2026/27), losses offsettable, reported on SA108. Algorithmic trading for own account needs no FCA authorisation. Very high-volume trading can rarely be reclassified by HMRC as a trade.

### (d) Common failure modes
The builder spends months on infrastructure and never states a falsifiable hypothesis or makes a decision. Others: overfitting; chasing more data instead of better questions; automation before validation; single-vendor dependence. **Antidote:** every build starts from a written hypothesis with a decision attached.

### (e) The credible middle path
Build the intelligence/monitoring system for slow, discretionary, long-horizon decisions: (1) track verticals via free feeds, (2) map overlay, (3) LLM/GDELT monitoring and alerting, (4) written research log feeding positions via a mainstream broker or ISA/SIPP. Uses AI for what it's good at, near-zero cost, avoids leverage traps, matches the one edge an individual has: time.

## Recommendations
1. **Weeks 1–4:** Python; EIA + USDA + PortWatch; Kepler map; one falsifiable hypothesis.
2. **Months 2–3:** 4–6 free feeds into DuckDB, Prefect, Grafana/Streamlit, GDELT + GPR alerts.
3. **Quarter 2:** backtest in VectorBT with costs; paper-trade via IBKR only if it survives.
4. **Scale spend only when a specific, recurring decision is blocked by missing data.**
5. **Never deploy autonomous execution.** Only consider more automation with a replicated, costs-included, 12+ month out-of-sample track record.

## Caveats
- Institutional prices are estimates or quote-only.
- LLM-trading-agent results are backtest-only and self-reported.
- Retail loss statistics are the single most important number in this report.
- Prediction markets (Kalshi, Polymarket) are not legally accessible to UK retail; UKGC (4 Feb 2026) classifies them as gambling requiring a licence neither holds.
- Tax and FCA rules are 2026/27; confirm with HMRC or an adviser.
