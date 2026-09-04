# INFONOMICS — CONTEXT PRIMER FOR EXTERNAL SESSIONS

**Version:** 1.1 · **Date:** 4 September 2026 · **Provenance:** built from the project-file spines (Layer A math companion, A₀ paper), the Drive checkpoint `02 — MASTER STATE 2026-08-22 (rev 2)`, and the AI Performance-Risk programme's `MASTER CANONICAL RECORD & ONBOARDING BIBLE v1.0` (27 June 2026). The EA Economics / Architecture Ledger track (Zenodo, Sept 2026) is deliberately excluded — it is firewalled from Infonomics IP. · **Author of the framework:** Abhineet Asthana (PhD candidate; UK)
**Purpose:** Self-contained reference document to be pasted into a separate chat session (e.g. a live trading application build) so that the session has an accurate picture of the Infonomics thesis, the framework architecture, the mathematics actually built, what is proven vs. conjectured, and what is dead. Nothing in this document is a claim beyond what the canonical project artefacts support.

**Handling:** This is unpublished personal IP held pending an IP carve-out. Keep it on personal infrastructure. Do not reproduce into vendor systems.

---

## 0. HOW TO USE THIS DOCUMENT

If you are a model or agent reading this as context:

1. Treat every mathematical claim with the epistemic tier attached to it. **[T1]** = established theorem in the literature, applied straightforwardly. **[T2]** = derived model with stated limitations. **[T3]** = conjectured analogy requiring empirical validation. A claim without a tier is a description of project state, not a mathematical claim.
2. Do not resurrect anything in §11 (Dead Approaches). Those were killed under hostile audit for principled reasons and the reasons are given.
3. Do not present **[T3]** items as results. In particular, the Hawkes-to-supra-Laplacian conjecture φ_ij = c_ij/(c_ij + κ_i) is unfalsified and must not be operationalised in any product.
4. Where the framework does not apply, say so. Section 14 gives an honest mapping of what does and does not transfer to a trading context.
5. The author's standards: viva-defensible, zero fabricated artefacts, zero false-progress signalling, brutal honesty over validation.

---

## 1. WHAT INFONOMICS IS

**One sentence:** Infonomics is the economics and science of information, with the core programme being a continuous, dynamic, flow-based mathematical framework for measuring information — data — as a quantifiable financial asset that can be valued, risk-assessed, securitised, and converted into a revenue-generating capital asset.

**The lineage.** The term and the foundational intuition come from Doug Laney (*Infonomics*, 2018), who argued data should be treated as an asset and proposed a set of valuation formulae. Laney's equations are *snapshots*: they value a stock of data at a point in time. The present framework is fundamentally different in kind — it is *continuous, dynamic and flow-based*. It models how information stock accumulates, decays, tips, defaults, and propagates risk across an enterprise and across the economy, using the same class of mathematics that finance uses for other capital assets.

**The methodological claim.** The novel contribution is *architectural synthesis*: identifying which established mathematical structures correctly formalise phenomena in information capital that currently have no rigorous quantitative treatment, and composing them into a consistent stack. This is explicitly modelled on how Black–Scholes (borrowing the heat equation and Itô calculus) and Markowitz (borrowing quadratic optimisation) worked historically: the mathematics existed; the synthesis did not. The framework is therefore honest that most of its components are **[T1]** results applied to a new domain, with a small number of **[T2]** derivations and a smaller number of **[T3]** conjectures marking where genuine novelty lies.

**The scope.** Data-as-capital is the core but not the entirety. The broader discipline covers:

- The measurement problem (how to put a defensible number on an information asset and its risk).
- The institutional problem (why markets for information risk-transfer have not formed, and what infrastructure would let them form).
- The macro problem (data as a hidden current-account item; "digital colonialism"; data infrastructure as a systemic-risk object requiring central-bank-style governance).
- The historical problem (why some polities built the measurement infrastructure that unlocked long-dated capital markets and others did not — the "1694 moment").

---

## 2. THE CORE THESIS — SEVEN CLAIMS

These are the load-bearing positions of the programme. Each is stated with its current epistemic status.

### 2.1 Information is a capital asset with stock-flow dynamics, not a snapshot
Data has a stock (what exists), inflows (origination), transformation (processing into higher-value forms), decay (staleness, inconsistency, obsolescence), and outflows. Valuation that ignores the dynamics is systematically wrong because the asset's future cash flows depend on the flow regime it is in. **[T2]** — modelled via the Layer A canonical equation (§5).

### 2.2 Non-rivalry is the defining property and breaks most inherited finance tools
Data can be used by many parties simultaneously without depletion (Jones & Tonetti 2020, AER). This is why: (a) ensemble methods borrowed from statistical physics diverge (§11); (b) "ownership" is the wrong primitive for data transactions (§12.2); (c) exclusivity in data markets is *manufactured* by contract, not natural. **[T1]** for non-rivalry itself; **[T2]** for the consequences.

### 2.3 Information assets exhibit irreversible tipping (fold catastrophe), not smooth degradation
Under scale-dependent contention in the processing pipeline, the equilibrium stock of an information asset undergoes a *fold* (saddle-node) bifurcation: a one-way, irreversible collapse to a degraded state, with hysteresis. This is *derived* from the Universal Scalability Law kinetics via the Centre Manifold Theorem, not assumed. It is a fold, not a cusp; the cusp is retained only as a phenomenological description of observed shapes. **[T1]** mathematics / **[T2]** application (§5.4).

### 2.4 Rights allocation follows measurement
A claim cannot be assigned against an asset that no accounting system recognises. Employees, customers, and other data subjects lack standing in data transactions not because of a policy choice but because the asset is not measured on any balance sheet. Build the measurement infrastructure and the rights question becomes tractable; without it, it is not even posable. This is the load-bearing claim of Paper One and the Spirit Aviation case (§12.2). **[T2]** — a Barzelian property-rights argument applied to information.

### 2.5 Measurement infrastructure is the binding constraint on risk-transfer market formation
Markets for transferring information risk (insurance, securitisation, derivatives on data assets) have not formed because no shared measurement infrastructure exists — not because demand is absent. Historical analogues: Lloyd's could not underwrite before Halley's mortality tables and marine loss registers; the Bank of England's 1694 charter was viable only because Huygens, Bernoulli and Halley had built the mathematics for long-dated debt. Infonomics Layers A/B/C are proposed as the analogous mathematical precondition for data-infrastructure governance regimes (DORA, UK Critical Third Party regime). **[T2]** historical-institutional argument.

### 2.6 Data-infrastructure coupling creates genuine systemic risk
Enterprise data estates are coupled through shared infrastructure (cloud, identity, CDNs, SaaS). Failures cascade. Empirically, the cascade multiplier (downstream cost ÷ direct cost) has been stable at roughly 4–10× across 2017–2025 incidents, and data-governance failure is the root cause in every audited case. Market structure (moat) determines survivability more than technical resilience. DORA and the UK CTP regime are read as first-generation central banking for data infrastructure. **[T2]** empirical / **[T3]** institutional analogy.

### 2.7 Infonomics is a post-industrial national strategy
For a post-industrial economy, the measurement, governance and capitalisation of information is the equivalent of what industrial policy was for manufacturing economies. Data rent flows are a hidden current-account item; reserve-currency-style "curse" dynamics apply (Keen); cloud capital as technofeudal rent (Varoufakis). **[T3]** — theory work, future chapters, not formalised.

---

## 3. THE FRAMEWORK ARCHITECTURE

**The programme has three tracks.** (1) The **core layer stack** below (A₀ → A → A.5 → B → C → D → GUM). (2) The **AI Performance-Risk Insurance programme** (§7A) — the flagship *application* of Infonomics: measurement infrastructure and pricing mathematics for insuring AI performance risk; it consumes Layer A₀ and adds its own papers and a Measurement Layer. (3) The **Empire / CAS knowledge base** (§12.4) — ~575K words of historical complex-adaptive-systems analysis intended as the "why should I care" instrument and hypothesis-validation base; unverified. A fourth body of work, Enterprise Architecture Economics, is a separate discipline and is not part of Infonomics.

The mathematical programme is a stack of layers. Each layer consumes the outputs of the one below and hands specified objects to the one above.

| Layer | Name | What it does | Status (Sept 2026) |
|---|---|---|---|
| **A₀** | Origination | Endogenises data ingress s(t): enterprise architecture as an operator on a multilayer temporal graph | v1.5 Bible, ~22.6K words, 25 sections. SSRN-ready pending DOI check and one companion-paper edit |
| **A** | Stock-Flow Dynamics | Canonical SDE for information stock; USL kinetics; fold; Weibull decay; Hawkes shocks; composition stability | Math LOCKED. Worked bible ~9.8K words; layman book 7 chapters finished. v3.4 patch (24 items) pending |
| **A.5** | AI Model Capitalisation | Models as vintage capital with seven depreciation drivers and a salvage floor | Complete |
| **B** | Valuation & Risk | Five components: income-DCF, fold regime, SFC accounting, MC first-passage default, systemic risk | v2.1 hardened, ~14K words; expandable to ~21K |
| **C** | Value of Information / Real Options | Use-conditional valuation of the option premium on data | **DEAD in current form.** Ground-up rebuild required. IICB is leading replacement |
| **D** | Network Effects, Velocity, Risk | Inter-organisational composition; liquidity of information assets | Not started |
| **GUM** | Grand Unified Model | Integration of A₀ → A → A.5 → B → C → D | Not started |

**The genuine unification (the causal chain).** The framework's coherent through-line is:

> **Architecture → Jacobian / supra-Laplacian eigenvalues → fold proximity → first-passage default → asset value.**

Architectural decisions (A₀) determine the coupling structure and ingress; those determine the Jacobian of the stock-flow system (A); the Jacobian's leading eigenvalue measures distance to the fold; distance to the fold drives default probability (B.4); default probability and the DCF give the asset value (B.1). Every arrow is derived, not asserted. A previously claimed unification via Kappen path-integral control and partition-function ensembles was **formally retracted** under hostile audit (§11).

---

## 4. LAYER A₀ — ORIGINATION

### 4.1 The problem it solves
Layer A treats data ingress s(t) as an exogenous forcing function — data "just arrives" at the analytical boundary. This violates causal closure (the architecture that determines what is collected is itself a strategic choice that feeds back into asset value) and prevents optimisation. Layer A₀ endogenises s(t).

### 4.2 Central formal object
Enterprise architecture is modelled as an **operator** on a multilayer directed heterogeneous temporal graph

> 𝓜 = (V, E, L, φ, ω)

with V nodes, E directed edges, L = six enterprise layers (physical, logical, data-plane, governance, organisational, economic), φ a typing function, ω edge weights. The full Layer A₀ five-tuple is A₀ = (𝓜, T, S, P, F): graph, temporal structure, signal space, Petri-net overlay, edge calculus.

Architecture Decision Records (ADRs) are formalised as double-pushout (DPO) graph-rewriting witnesses: an architectural decision is a rewrite rule applied to 𝓜.

### 4.3 Spectral machinery **[T1]**
The **supra-Laplacian** L_𝓜 of the multilayer graph governs diffusion of information across layers. Its Fiedler eigenvalue λ₂ measures algebraic connectivity. Inter-layer coupling strengths c_ij, compared against the Gómez crossover threshold c*, determine whether the estate is in the intra-layer-dominated or inter-layer-coupled regime. Calibration across three archetypes (BIAN-aligned bank, ARTS-aligned retailer, AI-first SaaS) finds c/c* large in all three: **the inter-layer-coupled regime is the normal operating regime for modern enterprise data systems**, which is why the supra-Laplacian is used rather than its intra-layer projection. The supra-Laplacian is proposed as a dimensionally coherent replacement for the informal notion of "data gravity". Hodge decomposition on the graph gives the Hodge 1-Laplacian Δ₁ and first Betti number β₁ (count of independent circular dependencies).

### 4.4 Temporal machinery **[T1]**
Enterprise events are bursty, with heavy-tailed inter-arrivals; M/M/1 queueing is not merely inaccurate but non-parameterisable when inter-arrival power-law exponent α ≤ 2. Replacement: Hawkes/G/1. The Hawkes process (Hawkes 1971) has conditional intensity

> λ(t) = μ + Σ_{t_i < t} g(t − t_i)

with baseline μ and excitation kernel g. Branching ratio n* = ∫g(τ)dτ; stationarity iff n* < 1; expected cluster size 1/(1 − n*). For incident cascades n* is the formal content of "cascading failure".

**Markovian embedding (§11.3 of A₀, closes a Layer A audit defect).** With exponential kernel g(τ) = α·e^(−κτ), the pair (x, λ) is an exact piecewise-deterministic Markov process: between events dλ/dt = −κ(λ − μ), at events λ jumps by α. The infinite-dimensional history collapses to one scalar because e^(−κ(t+s−t_i)) factorises. This makes Layer A's centre-manifold reduction (which requires Markovian state) applicable. A spectral-gap separation licenses the reduction and a transverse Lyapunov function establishes stability of the reduced dynamics. Holds *only* for exponential-family kernels or finite sums thereof — non-exponential kernels are open.

### 4.5 Process overlay **[T1]**
A Petri-net workflow overlay (GSPN) bridges to CTMC and Jackson/BCMP queueing models, giving Layer A its queueing triple (R, λ, μ). Object-centric process mining (OCEL 2.0; van der Aalst; Berti–Montali–van der Aalst 2024) closes the measurement loop: discovered event-log topology is the empirical graph against which 𝓜 is calibrated, and conformance/drift detection signals when architecture has shifted the origination regime.

### 4.6 Endogenisation of s(t) via active inference **[T2]/[T3]**
The firm is modelled as an agent selecting data sources to minimise expected free energy G(π), which decomposes into *epistemic value* (information gain about latent states) and *pragmatic value* (expected KPI improvement). The firm ingests data where the EFE gradient is largest. The Information Bottleneck functional (compression cost I(X;T) vs. predictive relevance I(T;Y)) is shown to be a special case of EFE, with its Lagrange multiplier β anchored to FinOps marginal compute cost, β = ∂C_compute/∂I(X;T). The Markov-blanket construction at organisational scale and the β-to-FinOps identification are **[T3]**. The paper engages the Biehl–Pollock–Kanai (2021) and Aguilera et al. (2022) critiques of the free-energy principle directly and distinguishes normative from metaphysical uses.

### 4.7 Thermodynamic floor **[T1]/[T2]**
The Still–Sivak–Bell–Crooks dissipation bound gives a physical floor on compute cost per useful bit; a dollar-transposed "Infonomics Second Law" follows, with σ_$ (marginal FinOps cost per useful bit) and I_nostalgia = I(X_past; X_state) − I(X_state; X_future) as the retained-but-useless information that retention policy modulates. Archetype ranges: σ_$ ~ 10⁻¹⁰–10⁻⁷ $/useful bit depending on estate type. **Caveat (locked):** thermodynamic pricing is a false friend — the Landauer bound (~10⁻²¹ J/bit) is ~20 orders of magnitude below real compute costs and cannot anchor dollar valuation. The SSBC bound is a floor on the cost *structure*, not a price.

### 4.8 Chaos refutation (§5.12 of the Bible) **[T2]**
The coupled origination-and-dynamics system was shown *not* to admit chaos in the composed reduction via a triangular-Jacobian argument. The remaining open edge is the coupled multivariate regime near Hawkes criticality (n* → 1), where a pre-registered largest-Lyapunov-exponent test is specified. No chaos claim is made either way.

### 4.9 Framework composition (§22) **[T1]/[T2]**
Layers compose as decorated cospans; four "seams" between layers are identified and the asymmetric-coupling repair is specified so that composition is well-defined.

### 4.10 The central conjecture **[T3]**

> **φ_ij = c_ij / (c_ij + κ_i)**

The Hawkes cross-excitation kernel between layers i and j (a temporal quantity measurable from event logs) is conjectured to be determined by the supra-Laplacian inter-layer coupling c_ij and the layer-i Hawkes decay κ_i (spectral/structural quantities measurable from the architecture graph). An exhaustive survey found no prior art for a specific algebraic relation between Hawkes branching structure and supra-Laplacian coupling. A pre-registered falsification protocol exists ("option b-2": stated as a design with the data precondition unmet, execution deferred — not a fake proxy test).

**Materially stronger than "unverified conjecture" (locked A₀ decision, carry verbatim):** the Seam 1 coherence condition in §22 Framework Composition is *algebraically identical* to φ_ij. That makes the conjecture the framework's **composition law** — the condition under which A₀ and A compose consistently — not an empirical guess bolted on. State it that way. Seam 2 defect and repair: the directed architecture graph supplies asymmetric coupling that a symmetric supra-Laplacian cannot consume; repaired with a three-branch asymmetry-graded decision tree using the **magnetic Laplacian** at intermediate asymmetry. The six-layer architecture model is deliberately EA-school-agnostic (do not align to TOGAF BDAT).

**The conjecture cannot currently be tested**: no public object-centric log carries the six-layer attribution required. It is unfalsified and must not be ported into any practitioner-facing or product work.

---

## 5. LAYER A — STOCK-FLOW DYNAMICS (MATH LOCKED)

### 5.1 Canonical equation

> **dx/dt = N · v(x) · h(t) + s(t) − d(x)**

- **x** — vector of information stocks by compartment (species) on a directed graph.
- **N** — non-rivalry mask Λ: encodes which transformations consume their input (ρ = 1, rival) and which do not (ρ = 0, non-rival). Jones & Tonetti (2020). **[T1]**
- **v(x)** — USL kinetics (Gunther 2008): throughput of transformation as a function of load. **[T1]** for the form.
- **h(t)** — human-capital multiplier: fraction of nominal capacity the workforce can realise. Handed up to Layer B as a risk factor.
- **s(t)** — data ingress. Exogenous in Layer A; endogenised by A₀.
- **d(x)** — decay operator. Canonical lineage form d(x) = μx + νx² (linear staleness + quadratic pairwise inconsistency); in the worked spine, per-species Weibull hazard (§5.5).

The ODE is the fluid limit of a tandem queueing network (Chen–Mandelbaum 1991; Dai 1995) by Kurtz's theorem, a.s. error O(ln N/N) in event throughput N. **[T1]**

### 5.2 USL kinetics
For a compartment with nominal rate μ, contention σ, coherency κ and normalisation p:

> v(x) = μx / (1 + (σ/p)x + (κ/p²)x²)

Michaelis–Menten is the κ = 0 special case. The κ term produces *retrograde throughput* — adding load reduces output — and is the sole source of the cubic below.

### 5.3 The USL cubic — genesis of the fold **[T2]**
At equilibrium s − dx − v(x) = 0 for one compartment with linear decay d. Multiplying through by the positive denominator D(x):

> −(dκ/p²)x³ + (sκ/p² − dσ/p)x² + (sσ/p − d − μ)x + s = 0    (A.2.4)

**Proposition (genesis of the fold).** (A.2.4) is a genuine cubic iff dκ ≠ 0. As (s, σ, κ, d) vary, the number of positive real roots changes between one and three; the transition occurs where the cubic discriminant Δ = 18ABCD₀ − 4B³D₀ + B²C² − 4AC³ − 27A²D₀² vanishes — the locus of a fold (saddle-node) bifurcation. Descartes' rule on sign pattern (−, ?, ?, +) gives one or three positive roots, consistent with a single fold separating a one-equilibrium regime from a bistable one.

**Load-bearing consequence:** the bifurcation originates in the USL κ cubic, *not* in the quadratic decay term νx². This is a locked correction.

### 5.4 Three-tier bifurcation
**Tier 1 — Fold via Centre Manifold [T1] math / [T2] application.** Scalar field f(x; α) = s(α) − dx − v(x) with single control α. Fold at (x*, α*) where f = 0 and ∂f/∂x = 0 (double-root condition, Δ = 0). Centre Manifold Theorem (Carr 1981; Guckenheimer–Holmes 1983) reduces to normal form ẏ = a₁(α − α*) + a₂y² + O(y³), with a₂ = −½v''(x*) ≠ 0 whenever κ > 0 (SN1) and a₁ = s'(α*) ≠ 0 (SN2, transversality). Sotomayor's conditions hold explicitly; rescaling gives ẏ = α̃ − y². **The fold is derived, not assumed.**

*Irreversibility:* for α < 0 no real equilibrium remains; the state departs to a distant attractor; restoring α > 0 does not retrace the path because the stable branch was destroyed — strict hysteresis.

*Detection:* as α → α*, f_x → 0⁻, recovery rate vanishes, lag-1 autocorrelation and variance rise — critical slowing down (Scheffer et al. 2009). **[T1]**. This is the operational early-warning signal the framework offers.

**Tier 2 — Cusp, phenomenological only [T2].** A causal cusp needs two independent controls and a triply-degenerate organising centre (f, f_x, f_xx all zero). The single-control USL equilibrium generically produces a fold (codim-1), not a cusp (codim-2). The cusp normal form ẋ = α + βx − x³ is retained as a topological classification of observed bimodality/hysteresis, in the Landau–Ginzburg tradition, with *no causal claim*. Falsifiability via Cobb–Grasman maximum-likelihood fit of the stationary density p(x) ∝ exp[(αx + ½βx² − ¼x⁴)/ξ] with AIC/BIC against linear and logistic alternatives; quantitative cusp claims **[T3]** pending that fit. Proposition A.3.2 shows a cusp can arise without a gradient assumption at a doubly-degenerate multi-compartment Jacobian (answers Zahler–Sussmann 1977).

**Tier 3 — Fenichel slow-manifold enrichment [T1]/[T2].** Where timescale separation is sharp (ε < 0.1: batch, micro-batch, Medallion, Lambda architectures), Geometric Singular Perturbation Theory (Fenichel 1979) gives a persistent invariant slow manifold and quantitative bifurcation curves. Streaming/Kappa systems (ε ≈ 0.1–0.5) fail the requirement and rely on Tiers 1–2.

### 5.5 Decay — Weibull staleness **[T1] form / [T3] application**
Each species i decays with Weibull hazard

> h_i(t) = (β_W,i/η_i)(t/η_i)^(β_W,i − 1),   d_i(x,t) = h_i(t) x_i

β_W = 1 exponential decay; > 1 wear-out; < 1 infant mortality. Series-system reproductive property: quality dimensions with common shape combine to a Weibull with scale η = (Σ η_i^(−β_W))^(−1/β_W). No published fit for data quality; default β_W = 1.

**Decay reframe (August 2026, testable, potentially a real contribution):** decay rate is a function of *signal specificity*, not age. Specific parameter values (fare levels, competitive regime, input prices) decay fast and suffer structural breaks; generic process/behavioural patterns (workflow structure, escalation paths, thread structure) decay slowly. Required modification: per-USE decay, d(x) conditional on deployment. Not yet in the locked spine.

### 5.6 Shocks — Hawkes, not compound Poisson **[T1]**
Exponential kernel: λ*(t) = μ + Σ φ(t − t_i), φ(u) = αe^(−βu), n* = α/β. Shocks enter decay as state-proportional jumps d_i(x,t) = h_i(t)x_i + x_i Σ_k J_ik dN*_k(t), J_ik ∈ [0,1].

**Proposition (Hawkes stability).** Unique stationary version with finite intensity iff n* < 1; then λ̄ = μ/(1 − n*) and expected cluster size 1/(1 − n*). Proof via Hawkes–Oakes cluster representation (Galton–Watson subcriticality). n* is the *contagion fraction* — the share of shock burden that is endogenous.

### 5.7 Stochastic version — Gaussian diffusion, CIR killed **[T1]**
The Kurtz central limit theorem gives Gaussian fluctuation with state-dependent variance

> Σ(x) = μx + 2νx²

**Not** a CIR √x form. The CIR noise model previously in the framework is discarded (locked correction). Consequence downstream: the CIR×OU product used in an earlier Black–Cox default model is non-Markovian; the √P obstruction is proven; Black–Cox is withdrawn and replaced by Monte Carlo first-passage (B.4).

### 5.8 Gap N1 — the νx² micro-foundation (resolved as demote-with-micro-foundation)
*Form* **[T1]**: mass-action propensity for 2X → Λ is a(x) = k·x(x−1)/2; Kurtz fluid limit gives ẋ ⊃ −νx², ν = k (Verhulst 1838; Bass 1969; Kephart–White 1991 — the form is not novel). *Mechanism* **[T2]**: pairwise inconsistency — conflicting record-pairs grow as C(x,2) ~ x²/2; per-pair conflict hazard φ and m units invalidated per surfaced conflict give ν ≈ ½φm. *Fencing*: the x² origin is the **same scale driver** as USL coherency κ (one slows flow, the other destroys stock), so (i) νx² is never a second bifurcation source; (ii) ν and κ calibrate jointly, never independently; (iii) preferably rehomed in the Weibull/DAG quality machinery; (iv) **[T3]** and non-load-bearing until ν is measured. Pending external review; not a proven theorem; changes no load-bearing result.

### 5.9 Composition — network small-gain **[T1]**
Subsystem Σ_i is input-to-state stable (ISS) if |x_i(t)| ≤ β(|x_i(0)|, t) + γ(sup_s |u_i(s)|). **Proposition (network small-gain, Dashkovskiy–Rüffer–Wirth 2010):** with gain matrix Γ = (γ_ij), if ρ(Γ) < 1 (linear case) the interconnection is ISS. Operationally: form Γ from steady-state DC gains; ρ(Γ) < 1 certifies stability and any γ_ij ≥ 1 *names the culprit coupling*. Replaces the earlier operadic-composition-as-primary approach. "Spectral unification" across Leontief/BCMP/ISS matrices is rhetorical only — three different matrices.

### 5.10 Quality propagation — DAG + common cause, not SIR
Error propagation is modelled on the lineage DAG with spectral radius ρ(A) and a common-cause-failure overlay (NUREG/CR-5485 alpha-factor lineage). SIR epidemic contagion was rejected as a category error. Handed to B.2 as a quality overlay. CrowdStrike (July 2024) is classified as a *broadcast* failure with recovery, not a fold.

### 5.11 Worked example (six-compartment Medallion, fully computed)
Compartments R (raw), C (curated), F (features), M (models), P (products), V (value), reactions R→C, C→P, R→F, F→M, M→P, P→V, V→R; all non-rival except V→R (ρ = 0.1); h = 0.85; Hawkes μ = 2/yr, α = 1.5, β = 3.0 ⇒ n* = 0.5, cluster size 2, λ̄ = 4/yr.

Equilibrium: R* ≈ 8.2, C* ≈ 2.0, F* ≈ 1.1, P* ≈ 0.55, V* ≈ 0.42 PB; M* ≈ 47 models. All Jacobian eigenvalues negative real part; spectral gap ≈ 0.037 ⇒ recovery half-life ≈ 19 days.

Bifurcation walk: raising documentation debt D_doc toward D_crit = 100 while cutting governance produces a near-zero eigenvalue at D_doc ≈ 84 (governance ≈ 60% of optimal); collapse of C and P to a degraded equilibrium; recovery requires D_doc < 72. **D_collapse ≈ 84 vs. D_recovery ≈ 72 — the irreversible hysteresis of the fold, concretely.** Separately, dropping h from 0.85 to 0.40 does *not* bifurcate — stocks drain smoothly until h ≈ 0.32 where the queueing threshold is crossed and waiting times diverge: a distinct failure mode, cleanly separated.

Composition check: DC-gain matrix ρ(Γ) = 0.82 < 1 ⇒ ISS. Largest gain serving←ML ≈ 0.71; feedback prep←serving ≈ 0.23.

### 5.12 Minimum viable estate — multiplicative **[T2]**
V(t) = N(t) × V_C(t): estate value is the product of the network/coverage term and the per-compartment value term, not a sum. Justified via Topkis (1998) supermodularity — the complementarity between breadth of coverage and depth of curation means neither has value without the other.

### 5.13 Hand-offs to Layer B (eight, each derived)
Stocks → B.1 DCF · eigenvalues → B.2 regime proximity (labelled fold-causal / cusp-phenomenological) · SDE + Hawkes → B.4 MC first-passage default · DAG ρ(A) → B.2 quality overlay · infrastructure adjacency + failure-mode tags → B.5 · SEEA pair (x, r) → B.3 · M_floor → B.1 floor and B.4 recovery · h(t) → workforce risk factor.

---

## 6. LAYER A.5 — AI MODEL CAPITALISATION (COMPLETE)

Models are vintage capital:

> dM/dt = h(t)·T(F, P) − δ_M(t)(M − M_floor),   T(F,P) = τ_F F + τ_P P

Three nested lifespans: technological ⊃ economic ⊃ accounting. Economic life is a slide down the use-cascade (frontier → distilled → commodity inference → batch → scrap) to M_floor — a *staircase*, not a cliff. Seven drivers shape δ_M and set M_floor (not additive rates): staleness, capability drift, training-set obsolescence, regulatory deprecation, security degradation, energy-cost inflation, replacement competition. Regulatory obsolescence can push M_floor → 0, converting the staircase into a fold. Empirical anchors: capability price falls ~40×/yr (task-dependent 9×–900×, Epoch AI); fixed-capability inference fell ~280× in ~18 months (Stanford HAI 2025). M_floor sets B.1 recovery basis and B.4 loss-given-default = 1 − (durable-capability fraction). **[T1]** economics / **[T2]** application.

---

## 7. LAYER B — VALUATION & RISK (v2.1 HARDENED)

### B.1 Income-based DCF
**Primary method: with-and-without.** Value the firm with the information asset and without it; the difference is the asset's income contribution. Cost approach as floor (M_floor, salvage). Market anchoring where observable. Peer-attribution and circular DCF **both failed under audit** — do not use. Cite Damodaran; Crouzet & Ma (2023) on intangible capital; OECD Transfer Pricing Guidelines Ch. VI; AICPA PPA Guide. Realistic range for a major-platform data asset is ~$10–40B, not the $52–76B earlier drafts produced.

### B.2 Fold regime classifier
Consumes Layer A eigenvalues. Regime classes: stable / approaching fold / post-fold. **No reversible branch** — the classifier must not contain a bounce-back scenario, because the fold is irreversible. Where recovery exists it is a staircase to M_floor, not a return to the prior state. Quality overlay from DAG ρ(A).

### B.3 Stock-Flow Consistent accounting
Godley–Lavoie style SFC matrices for information assets, with SEEA/SNA 2025 dual-stock treatment and the China 2024 enterprise data-asset accounting standard as the live regulatory anchor. Keen–Minsky rejected for this layer.

### B.4 Monte Carlo first-passage default
Default = first passage of the (Layer A SDE + Hawkes) asset-value trajectory below a barrier. Black–Cox closed form **withdrawn** (CIR×OU product non-Markovian; √P obstruction proven). Recovery/LGD from M_floor.

### B.5 Systemic risk
Brummitt coupled catastrophes + Buldyrev interdependent-network percolation. Hosts the propagation mechanism. Empirical "gauntlet" finding across 2017–2025 cases: cascade multiplier 4–10× stable; market structure/moat determines survivability; data-governance failure is root cause in every case.

**Pending [P1] rework triggered by Layer A lock:** B.2 fold regime with no reversible branch; B.1/B.4 consume M_floor; B.5 hosts propagation; framework-wide reversibility audit.

---

## 7A. THE AI PERFORMANCE-RISK INSURANCE PROGRAMME (flagship application, June 2026)

**Source:** `AI INSURANCE PROGRAMME — MASTER CANONICAL RECORD & ONBOARDING BIBLE v1.0` (27 June 2026), Drive folder `1ok6DWSmbt0EeKQta-WiQdiphwEhNk8Vh`. This programme applies Infonomics to a concrete market: the measurement and data-utility layer that must exist before anyone can price insurance on AI systems at scale ("the actuarial register / Lloyd's register for the AI era"). Its tier discipline is the same as the core: every **structural** result is [T2] and hostile-audited; every **magnitude** is [T3] and pilot-gated; no structural result depends on a magnitude. Its own verdict on itself: *"internal structure is titanium; it is not bedrock; only a pilot moves [T3] to bedrock."*

### 7A.1 Components and stack
| Component | One line | Status (June 2026) |
|---|---|---|
| **Measurement Layer** | What counts as a measurement of AI risk; taxonomy; composition calculus; value of information. Produces the registry schema. | Four strata LOCKED + keystone + seam audit + kill-memo |
| **Companion I** | The accumulation problem: correlated AI failures do not diversify away | v1.1.1 audited; calibrated not validated |
| **Paper B** — "Pricing the Drift" | Pricing mathematics for single-model AI performance warranties | Canonical v2.2; numbers independently reproduced (Level 2 closed) |
| **Paper C** — "Institutions Are the Product" | Mechanism design: institutions set insurability; what carriers buy | Structurally complete; sign-off pending one pass |
| **Paper A** — "Why Now" | Market-formation theory; loss register as the missing co-necessary condition | Canonical v2.1; PARKED behind IP gate |
| **Layer A₀** (Infonomics core) | Architecture-as-operator formalism, used by Paper C for "decoupling" | v1.5 canonical |

**Strategic pivot (Session XXIII):** order flipped from *theory → insurance product → measure the world* to **measure the world → discover the mechanism → design the insurance**. The defensible asset is pooled cross-carrier loss/dependency data, not the mathematics ("complexity is not the moat; the data position is"). Two-sided model: carriers buy *benchmarking*, enterprises buy *attestation*. The central bet: foundation-model concentration persists (FM-HHI ≈ 0.285 vs cloud HHI ≈ 0.171); fragmentation to local open-weight models deflates the peril. Note on naming: this programme's Papers A/B/C are distinct from the core track's Paper One/Two/Three.

### 7A.2 Companion I — Diversification Impossibility **[T2]**
Under conditional independence given upstream shocks,

> Var(S/N) = (systematic term) + (1/N)(idiosyncratic term)

The idiosyncratic term diversifies at 1/N (Gordy/Vasicek); the systematic term → σ²·[HHI + ρ(1 − HHI)] under homogeneity and never diversifies. σ²·HHI is the ρ = 0 lower bound only (quoting it as the general floor is DEAD). The variance floor is set by upstream market structure, not book size. Correlation is in *event occurrence*, not loss direction. Mitigation: dual-homing fraction f with an independent fallback removes accumulation variance; fallback covenant discount 75/68/60/52% at fallback-correlation ρ_fb = 0/0.1/0.2/0.3 (f = 0.5) — with a haircut because popular fallbacks are themselves hubs.

### 7A.3 Paper B — pricing mathematics (verified numbers)
Warranty primitive W = (θ, T, M, ℓ, C_min, LGD): error-rate threshold, observation cadence, attested measurement protocol, per-breach indemnity, attachment, loss-given-default. Three failure regimes priced by different machinery — (1) gradual drift → subordinator/renewal; (2) clustered operational shocks → **Hawkes** overlay; (3) upstream silent updates → jump peril. Conflating them was the original error.

- **Dependent breaches (Case A) [T2], reproduced.** Quarterly evaluations within one retraining year share one drift path: X_k = √ρ·Z + √(1−ρ)·ξ_k, breach iff X_k > z_k (Vasicek one-factor). Marginal breach probabilities unchanged so pure premium unchanged; claim-count variance rises. At ρ = 0.7: E[N] = 0.13761; SD ratio 1.23×; SD-principle premium +13%; P(N ≥ 2) up ~5.5×. **Comonotonic ceiling [T1]:** Var(N)_max = 0.2395 under any dependence — this killed an earlier +32% / 1.56× / ~4× claim (implied Var = 0.305 > ceiling, infeasible).
- **Hawkes clustering [T1].** Mean intensity μ/(1−n*), variance rate μ/(1−n*)³, Fano factor 1/(1−n*)². An expected-value-principle carrier underprices clustered risk by up to ~35% while believing it fully priced.
- **Anti-gaming is institutional, not analytic [T1/T2] (Prop 1.2).** No scoring-rule property prevents adversarial gaming of a self-reported benchmark under stake. Defences: held-out eval rotation with cryptographic commitment, contamination audits, third-party attestation.
- **κ_perf — performative variance inflation [T2], a bracket.** When a deployed model changes the world it is later retrained on, estimation variance inflates by a factor between floor 1/(1−ρ_c²) (fresh data each requote) and ceiling 1/(1−ρ_c)² (fully reused data): [2.78, ~25] at ρ_c = 0.8. Interior governed by data-refresh fraction r — an institutional lever. (A single κ_perf = 142 is DEAD: unbounded-memory artefact.)
- **Retraining covenant [T2].** Retraining is imperfect repair with regression probability q; regression-test gate is both risk control and premium lever; discount 73–88% (a 93% figure assuming perfect reset is DEAD).
- **Securitisation [T2/T3].** AI-performance ILS feasible at 2–3.5× the property-cat multiple (~2.13× fwd-2026), decaying toward ~2× as the peril matures.
- **Notation warning:** Paper B's d and r collide with Paper C Part 1's d and r — different objects.

### 7A.4 Paper C — institutions are the product
- **Theorem C.1 [T2-structural]:** f_min(p₀, s) = (φ_min − ψ((b − κ' − s·r)₊ / (p₀·d)))₊. Audit probability p₀ and experience-rating sensitivity s lower-bound the tail-density floor f_min — which is exactly the regularity condition Paper B's pricing CLT needs. Institutions literally make the mathematics hold; as p₀ → 0, f_min → 0.
- **Part 2:** Parshani–Buldyrev–Havlin interdependent-network percolation on a Barabási–Albert stack. Under a targeted shock (a real FM update hitting the shared hub) the **shared-hub single point of failure is the primary peril** (survival 0.71/0.41/0.10 at top-5/10/15% hub removal [T3]); the coupling cliff (q_c ≈ 0.7) is secondary. Two mitigations both required: decoupling (the A₀ operator) for the cliff; de-concentration (named-model caps, HHI monitor, independent fallback) for the hub.
- **Master Theorem:** with centrality-weighted institutional floor F_w = Σ(deg_i/Σdeg)·f_min,i > 0, a stack is reservable iff q_eff ≤ q_c^ES. Three-rung ladder eliminates "uninsurable": **Reserve** (q_eff < q_c^ES) / **Securitise** (q_c^ES ≤ q_eff < q_c^perc) / **Extreme**. Institutions move the cliff (F_w enters q_c^ES). After the Audit #26 re-pin (both quantities on the coupling-mass axis; pure path-survival rule): q_c^ES = 0.162 at band B = 0.40, M_min = 0.098 — the marginal band is **wide**, because construction uncertainty (ρ_prop) dominates sampling noise ~24× until a pilot pins it. Earlier q_c^ES 0.079/0.151/0.214 and "band thin" are DEAD.
- **Moat re-attribution:** a published mechanism-design theorem cannot prove a moat. Paper C proves the attestation function is *necessary*; Paper A claims the *operator* of a necessary function is defensible (rating-agency model) — an empirical bet, not C's theorem. Open work item **BS-7**: anti-capture funding model for the attestor (issuer-pays trap, 2008 precedent).

### 7A.5 The Measurement Layer (the frontier)
Everything is anchored to ψ(L), the underwriting-relevant functional of the true loss distribution; a signal has value only insofar as it informs ψ.

**Part 0 — admissibility [LOCKED v0.3].** An instrument X is an admissible risk measurement iff it passes all five: **A1** observable through the deployment interface; **A2+A3** information survives attestation, I(X_attested; ψ) ≥ ρ_min·I(X_clean; ψ) with I(X_clean; ψ) > 0; **A4** manipulation-resistant under stake, cost_of_gaming ≥ κ·E[indemnity gain]; **A5** construct stability — a tripwire that fires when the instrument's meaning rots (benchmark contamination, spec drift) while it still returns healthy-looking numbers. Well-posedness: admissibility is judged against the contract-specified definition of ψ and a posited generative model, both fixed a priori. **Consequence [T2]:** model internals (weights, gradients, loss-landscape sharpness) fail A1 and the reproducibility half of A2+A3 and are inadmissible *by definition*, regardless of predictive power; provenance signals (retrain cadence, distribution shift) are admissible. Every admissible instrument is a tuple (estimator, estimand, sampling model, two-term precision [sampling variance + population-shift variance], A5 tripwire, attestation tuple) — this tuple is the registry's atomic row. Experiment 0.A: naive binomial CI coverage falls from 95% to 0.9% at +3pp deployment drift; the second precision term restores it.

**Part 1 — taxonomy [LOCKED v0.3].** Two axes: supply-chain layer (Foundation / Serving / Adaptation / Orchestration / Application / Governance) × lifecycle stage (Provenance / Deployment / Operation / Maintenance / Upstream-Dependency); ~21 risk classes. Instruments in different cells carry +366% more joint information than the best single cell. **Irreducibility ceiling [T2]:** perfect knowledge of every latent factor explained only ~30% of loss entropy → the layer estimates distributional functionals, never individual losses. Governance is a transverse *multiplier* (doubles other rows' retained information), not a column. Tier-A classes: RC-4 fallback independence; RC-5 cross-book accumulation (the moat row); RC-6 hidden-hub convergence under load.

**Part 2 — composition calculus [LOCKED v0.2].** Within a stack contributions add on the logit scale; the tail is driven by a shared common factor. Across a book, Var(S/N) → σ²·HHI + σ²/N (reproduces Companion I: 0.292 vs target 0.286). No-double-count: RC-4/5/9 are multiple indicators of one shared-hub factor, combined via a measurement model, not summed (naive summing triple-counts 3.6×). **Mandatory disattenuation:** noisy factor estimates bias loadings toward zero; the first combine recovered 0.83× true variance and the gate failed; dividing by indicator reliability Var(H)/Var(Ĥ) gave 1.002. Omitting it under-prices the catastrophe tail ~15–20%. Tail dominance: at N = 5,000 policies book risk is ~1,430× more sensitive to the hub factor than to any idiosyncratic row.

**Part 3 — value of information [LOCKED v0.2].** VoI(measurement) = reduction in posterior variance of ψ net of cost. VoI of idiosyncratic measurements collapses with book size; VoI of the hub cluster is flat (ratio 8 at N = 10 → >2,000,000 at N = 5,000). **Optimal cadence Δ* = √(2c / (k·d²))** — scales as 1/drift; fast-drifting rows measured ~16× more often than slow ones. Precision: push sample size until marginal VoI = marginal cost. VoI is the price ceiling for each data feed.

**Seam audit:** Part 3's VoI ratio equals the *square* of Part 2's tail-dominance ratio (1430² = 2,044,900) exactly — two independently built experiments lock via VoI ∼ sensitivity², a relationship neither was built to satisfy. **Kill-memo** (attacking the premise): survived, not unconditionally — fragmentation, market self-mitigation and incumbent data race are existential and pilot-only.

### 7A.6 Verified-numbers table (quotable) and dead-numbers quarantine
Live: +13% / 1.23× / ~5.5× (ρ = 0.7); E[N] = 0.13761; Var(N)_indep = 0.12796; P(N≥2)_indep = 0.00456; comonotonic ceiling 0.2395; κ_perf ∈ [2.78, 25] at ρ_c = 0.8; covenant 73–88%; fallback 75/68/60/52%; FM HHI 0.285, cloud 0.171; q_c^ES 0.162, M_min 0.098 [T3]; hub survival 0.71/0.41/0.10 [T3]; measurement-layer magnitudes all [T3] illustrative.
Dead (never quote): +32%/1.56×/~4×; Var(N) = 0.305; 0.12477 / 0.00756; 93% covenant; κ_perf = 142; q_c^ES 0.079/0.151/0.214; M_min ≈ 0.005 / "band thin"; non-isolation survival rule; κ-product rule as verified; "coupling cliff primary"; "uninsurable"; "measurement is THE binding constraint" (softened in Paper A to one of four co-necessary conditions: measurement, capital appetite, legal clarity, demand); "performativity doesn't inflate variance"; σ²·HHI as the general floor.

### 7A.7 Standing constraints
No public disclosure (SSRN, patent) until an employer IP carve-out is secured in writing — pilots, theory, and carrier conversations are allowed. Never re-admit model internals as measurement axes. Audit #9 rule: never trust a re-typed mechanism; gate every script against a known-good number.

---

## 8. LAYER C — VALUE OF INFORMATION / REAL OPTIONS (DEAD; REBUILD REQUIRED)

### 8.1 What died and why
- **Partition-function ensemble** Z = Σ e^(−S/λ): diverges for non-rival assets — exponential overcounting because the same data can be in every deployment simultaneously.
- **Kappen path-integral control**: requires a matched noise-control channel condition that is physically impossible for economic systems.
- **Bayesian Model Averaging**: category error — designed for competing statistical models, not competing algorithms/deployments.
- **Sheaf-theoretic consistency**: empty formalism — topologically trivial base space.
- **"Engine 5"**: was never defined.

### 8.2 What survives
Monte Carlo, dynamic programming, Shapley values (conditional on a well-posed cooperative game).

### 8.3 The rebuild direction — use-conditional valuation
Value is a function of *use*, not of the asset in isolation. Rebuild as a set of **named finite deployments**, each with its own exercise structure and decay clock. The option premium on a corpus is the sum over deployments of the option to derive first.

### 8.4 The IICB — leading replacement candidate (Paper Three)
The **Information Inverse Confidence Bond** prices the divergence between stated confidence in an information product and realised outcome, via proper scoring rules. It is both a mechanism-design contribution and the leading candidate to anchor the rebuilt Layer C.

### 8.5 The Spirit Aviation scope correction
When a firm is dead, income-DCF → 0, so *all* observed value is option value. Layer C becomes **more** relevant in liquidation, not less. The Spirit auction (§12.2) is a rare observable market price for a nearly pure data option premium.

---

## 9. LAYER D AND THE GRAND UNIFIED MODEL

Not started. Layer D will scale the network small-gain result to inter-organisational composition and add velocity/liquidity dynamics for information assets. GUM integrates all layers after D.

---

## 10. CONFIRMED NOVEL CONTRIBUTIONS

1. **Hawkes processes applied to regulatory-enforcement data** — zero prior art found. GDPR enforcement (n ≈ 2,800 events): ΔAIC = 244 vs. inhomogeneous Poisson — decisive evidence of self-excitation. **Caveat:** branching ratio n* = 0.987 is likely inflated by monthly aggregation; true value probably 0.2–0.5 with daily data. Needs full CMS Enforcement Tracker daily data + Ogata residual diagnostics before any publication claim.
2. **The full causal chain** architecture → eigenvalues → fold → default → asset value, each step derived.
3. **CRNT accounting + Kurtz-CLT variance + unified ledger** as a framing (the νx² form itself is not novel).
4. **The Hawkes-to-supra-Laplacian conjecture** φ_ij = c_ij/(c_ij + κ_i) with pre-registered falsification protocol — **[T3]**, untested.
5. **Per-use decay** d(x) conditional on deployment (decay reframe) — proposed, testable, not yet built.
6. **Rights-allocation-follows-measurement** as the load-bearing institutional claim.

---

## 11. DEAD APPROACHES — DO NOT RESURRECT

| Approach | Why it died |
|---|---|
| Kappen path-integral control | Matched noise-control condition impossible for economic systems |
| Partition-function ensemble | Diverges for non-rival assets |
| Bayesian Model Averaging in Layer C | Category error |
| Sheaf-theoretic consistency | Empty formalism |
| "Engine 5" | Never defined |
| CIR √x noise in Layer A | Kurtz CLT gives Gaussian μx + 2νx² |
| Black–Cox closed-form default | CIR×OU non-Markovian; √P obstruction |
| SIR quality contagion | Category error → DAG + common cause |
| Compound-Poisson shocks | → Hawkes |
| Michaelis–Menten as primary kinetics | → USL; MM is κ = 0 case |
| Operadic composition as primary | → network small-gain |
| Cusp as causal mechanism | Codim-2 not earned by single control; fold is causal |
| Cusp deleted entirely | Over-correction; retained phenomenologically |
| "Spectral unification" as one matrix | Rhetorical only — three different matrices |
| "Decay-as-geodesic" | Dressing on the staircase, no content |
| Peer-attribution DCF; circular DCF | Failed audit |
| Keen–Minsky in Layer B | Rejected |
| μx + νx² as bifurcation source | Bifurcation is from USL cubic |

---

## 12. EMPIRICAL ANCHORS AND LIVE CASES

### 12.1 GDPR enforcement Hawkes fit
See §10 item 1. This is the framework's strongest empirical result to date and its caveats are load-bearing.

### 12.2 Spirit Aviation / Google (live, SDNY, 2026)
Google won a $10m §363 bankruptcy auction for Spirit's enterprise dataset: ~100m emails, ~500m Teams chats, ~80K email accounts, ~175K employee records back to 1986, ~3.4m payroll records, ~30m lines of code with dev metadata, revenue-management systems, pricing models, booking curves, pricing on ~7.2bn competitor flights, Navitaire (190m PNRs, 7.5bn transactions). Customer/loyalty data excluded (privacy policy constrained the estate). De-identification by a third party paid by Google, certified to California standards; referential integrity across datasets *deliberately preserved*. Hearing adjourned to 9 September 2026 after AFA-CWA limited objection. Judge Sean H. Lane.

Analytical positions:
- **Ownership is the wrong primitive.** What transferred is a bundle: copyright in compilations and code, trade secret in pricing models, contractual use right.
- **Exclusivity is manufactured.** The corpus is non-rival; the auction sold a contractual monopoly over the exclusive right to derive first.
- **De-identification engineers rights out rather than buying them out**: no personal data → no data subject → no rights. Linkage was preserved because linkage *is* the value. Asset value as a function of identifiability is a genuinely novel, unformalised thread.
- **Rights allocation follows measurement.** Employees' lack of standing is downstream of the measurement failure, not a policy choice.
- **Bid spread $5m → $10m → $12.5m** is market formation without measurement infrastructure, visible in real time — the binding constraint visibly binding.
- Use as illustration (Paper One) and Layer B with-and-without *stress test*, not as calibration: a liquidation price is a floor observation, not a value. Slots/HQ ratio comparisons are rhetorically excellent but analytically empty (rivalrous, regulated real assets are not valid denominators for a non-rival corpus).
- Layers A/A₀ genuinely do not apply to a dead firm with no flow. Say so.

### 12.3 Empire / CAS knowledge base (second roadmap; unverified)
~575,000 words across nine complex-adaptive-systems domains × three phases (Rise / Peak / Decline) for Mongol, Tang, Byzantine, Ottoman, Spanish Habsburg, Dutch, British, American, and CCP China; Portuguese incomplete. ~89% complete with **zero verification pass** — a full multi-agent verification system was specified and never run. Role: the "why should I care" instrument for corporate leaders; the 1694 Bank of England case is the narrative vehicle; Step 4 ("mathematify the framework") is where it was meant to meet Layers A–D. Live theoretical bridge, written down nowhere else: CAS may be a layer *above* A₀, endogenising the ADR-driven rewrite rules A₀ treats as exogenous. Decision required: verify, scope down, or formally park. Nothing from this corpus should be cited as established.

### 12.4 Conceptual threads raised and not yet formalised [MEMORY-grade, not documents]
- **Three-tier global AI economy:** frontier-lab nations (US, China) / data-capital nations (India, Vietnam, Philippines) / broker nations (UAE, Singapore). Feeds "Digital Colonialism 2.0".
- **Data exchange / marketplace** — four structural weaknesses already identified: non-rivalry (selling creates no scarcity); measurement *reveals* value without *transferring* it; monopsony (few labs, millions of substitutable suppliers); firm-level pricing ≠ worker-level compensation. Needs a coordination layer (producer blocs, data trusts, enforceable licensing) on top of measurement.
- **National balance-sheet hypothesis:** developed nations hold ~$10–40T of information capital invisible to markets and governments, producing apparent fiscal stress despite real wealth. Candidate opener for the book's business case.
- Erasure / compliance-driven deletion costs are underweighted (small, fixable modelling gap). IACS mutual-recognition model for AI measurement institutions; the issuer-pays trap; layered insurance objects across the physical-to-AI stack.
- Lost artefact: Alphabet $80B raise as a live test of Paper One — rebuild offered, not taken up.

### 12.5 Systemic-risk gauntlet (2017–2025)
Cascade multiplier 4–10×, stable. Governance failure as root cause in every case. CrowdStrike 2024 = broadcast/recovered, not fold.

---

## 13. EPISTEMIC AND PROCESS STANDARDS

- **Three-tier classification** on every load-bearing claim: [T1]/(a) established theorem; [T2]/(b) derived model with limitations; [T3]/(c) conjectured analogy. Also written [THEOREM]/[MODEL]/[ANALOGY]. This is a defence mechanism, not a weakness.
- **Hostile audit** is the mandatory quality gate before any integration or publication. Several major components (Layer C, CIR noise, Black–Cox, Kappen, cusp-as-causal) were killed by it.
- **Zero fabricated artefacts; zero false-progress signalling.** Never claim a background task is running when it is not. Never present a [T3] item as a result. Never invent citations.
- **Spine first, derivative second.** Book-length working artefacts (bibles, layman books, papers) are derived from locked technical spines so they never contradict.
- **Sequence discipline**: one thing at a time; park properly.

---

## 14. RELEVANCE TO A LIVE TRADING APPLICATION — HONEST MAPPING

This section exists because the framework was built to value *enterprise information assets*, not to generate market signals. The following is what transfers and what does not.

### 14.1 What transfers directly

**Hawkes self-excitation (Layer A §5.6, A₀ §4.4) [T1].** Hawkes processes are standard in market microstructure (order-flow clustering, volatility clustering, flash-crash endogeneity). The framework's contribution is not the Hawkes machinery itself but the discipline around it: (i) the branching ratio n* as *contagion fraction* — the share of activity that is endogenous vs. exogenous; (ii) the aggregation caveat — n* estimates from coarse-grained data are inflated (the GDPR n* = 0.987 is the framework's own cautionary example); (iii) Ogata residual diagnostics before any claim. If the trading app fits Hawkes models, these three points apply verbatim.

**Critical slowing down as early warning (Layer A §5.4) [T1].** Rising lag-1 autocorrelation and variance as a system approaches a fold is generic (Scheffer et al. 2009) and is used in some regime-change detection literature. The framework's specific contribution is the insistence that a fold has *no reversible branch* — if the app's regime classifier contains a "bounce back to prior regime" state after a genuine fold, it is mis-specified by the framework's standards.

**Fold vs. staircase distinction (Layers A/A.5/B.2).** Irreversible collapse (fold) vs. stepwise decline to a floor (staircase) are different objects with different recovery structures. Mislabelling one as the other is the most common error the framework's audits found.

**Small-gain composition (Layer A §5.9) [T1].** For any multi-component system (multiple models, strategies, data feeds feeding each other), ρ(Γ) < 1 on the DC-gain matrix certifies input-to-state stability, and any γ_ij ≥ 1 names the destabilising coupling. Directly applicable to strategy-portfolio feedback and to model-on-model dependency in a trading stack.

**Performative feedback — κ_perf (§7A.3) [T2].** A trading model that moves the market it is later retrained on is the textbook performative-prediction case (Perdomo et al.). The programme's result: estimation variance inflates by a factor bracketed by 1/(1−ρ_c²) and 1/(1−ρ_c)², with the interior set by the data-refresh fraction. Any backtest that ignores this is over-confident by that factor. This transfers verbatim.

**One-factor accumulation / HHI (§7A.2, §7A.5) [T2].** For any book of strategies, models or positions sharing an upstream dependency (a data vendor, a foundation model, a venue), the systematic variance term is set by concentration (HHI) and does not diversify with N. The no-double-count rule (multiple indicators of one shared factor are combined via a measurement model, not summed) and mandatory disattenuation (noisy factor estimates bias loadings toward zero and under-price the tail ~15–20%) apply directly to factor-risk aggregation.

**Value-of-information cadence (§7A.5) [T2].** Δ* = √(2c/(k·d²)) — measure fast-drifting signals more often, and push precision on whatever the book is most sensitive to. The VoI table is the budget allocation rule for data feeds.

**Admissibility tests A1–A5 (§7A.5) [T2-as-definition].** Before a signal enters the app as a risk input: is it observable through the interface you actually have; does its information survive whatever attestation/verification you can do; is it manipulation-resistant under stake; and does it carry a construct-stability tripwire for when its meaning rots while the numbers still look fine? The A5 tripwire is the one most trading stacks lack.

**Monte Carlo first-passage (B.4).** Default/drawdown-barrier probability via simulation of the full trajectory rather than a closed form whose Markov assumptions may fail. The framework's warning: check whether the product of your driving processes is actually Markovian before using any closed-form barrier result.

### 14.2 What transfers as a framing, not as a model

**Data-as-capital / with-and-without valuation (B.1).** Useful for valuing the app's *own* data and model assets (feeds, alt-data, trained models) — with-and-without is the right method, M_floor the right salvage concept, and the seven A.5 depreciation drivers the right checklist for model decay. Not a pricing model for traded instruments.

**Per-use decay reframe.** Decay rate is a function of signal specificity, not age. Specific parameter values (levels, regimes) decay fast and break structurally; generic behavioural patterns decay slowly. This is a plausible lens for alpha decay across signal types but is **proposed, not built** — it is not in the locked spine.

**Use-conditional option value (Layer C rebuild direction).** The option premium on an information asset is a sum over named finite deployments each with its own exercise structure and decay clock. Framing only; Layer C is dead and the rebuild has not been done.

**Rights-follow-measurement, manufactured exclusivity, de-identification frontier (§12.2).** Relevant if the app deals in alternative data licensing or data provenance. Institutional analysis, not math.

### 14.3 What does NOT transfer — do not use

- **The φ_ij conjecture.** [T3], unfalsified, untestable with available data. Must not be operationalised.
- **Layer A₀ active-inference endogenisation of s(t).** Built for enterprise data-source selection; [T2]/[T3]; no claim that it models market participants.
- **Layer C in any prior form.** Dead.
- **Any calibration numbers from the worked example (§5.11) or archetypes (§4.3).** Composite fictions for an enterprise Medallion estate. Not market parameters.
- **The USL cubic as a model of price dynamics.** The fold derivation is for *processing-pipeline* contention under load. There is no claim that asset prices follow USL kinetics. Borrowing the fold *language* is fine; borrowing the *cubic* is a category error.
- **Any claim that Infonomics produces trading signals.** It does not. It is a valuation-and-risk framework for information assets with some machinery ([T1] items above) that happens to be shared with market microstructure.

### 14.4 Where a trading app could genuinely contribute back
- Daily-resolution Hawkes fits with Ogata residuals would be a methodological template the framework needs (the GDPR n* recalibration is an open [P2] item).
- Empirical evidence on alpha decay by signal specificity would be the first data against the per-use decay reframe.
- A high-frequency observed market for any information-derived asset would be a rare calibration observation for the Layer C rebuild — the Spirit auction is currently the only one.

---

## 15. NOTATION

| Symbol | Meaning |
|---|---|
| x | Vector of information stocks by compartment |
| N, Λ | Non-rivalry mask; ρ = 0 non-rival, ρ = 1 rival |
| v(x) | USL kinetics μx/(1 + (σ/p)x + (κ/p²)x²) |
| μ, σ, κ, p | Nominal rate, contention, coherency, normalisation |
| h(t) | Human-capital multiplier |
| s(t) | Data ingress (exogenous in A, endogenised in A₀) |
| d(x) | Decay operator; lineage form μx + νx²; spine form Weibull h_i(t)x_i |
| ν | Pairwise-inconsistency destruction coefficient ≈ ½φm; coupled to κ |
| Σ(x) | Kurtz-CLT diffusion variance μx + 2νx² (Gaussian) |
| Δ | Cubic discriminant; Δ = 0 is the fold locus |
| α, α* | Control parameter and its fold value |
| β_W, η | Weibull shape and scale |
| λ(t), λ*(t) | Hawkes conditional intensity |
| n* | Hawkes branching ratio ∫g = α/β; contagion fraction |
| J_ik | Shock impact fraction on stock i from process k |
| Γ, ρ(Γ) | DC-gain matrix and its spectral radius (small-gain) |
| ρ(A) | Spectral radius of lineage DAG adjacency (quality propagation) |
| M, M_floor, δ_M | Model stock, salvage floor, model depreciation rate |
| 𝓜 = (V,E,L,φ,ω) | A₀ origination graph |
| L_𝓜, λ₂ | Supra-Laplacian; Fiedler eigenvalue |
| c_ij, c* | Inter-layer coupling; Gómez crossover threshold |
| φ_ij, κ_i | Hawkes cross-excitation kernel; layer-i decay — conjecture φ_ij = c_ij/(c_ij + κ_i) [T3] |
| G(π) | Expected free energy of policy π |
| β (IB) | Information Bottleneck multiplier = ∂C_compute/∂I(X;T) |
| σ_$ | Marginal FinOps cost per useful bit |
| Δ₁, β₁ | Hodge 1-Laplacian; first Betti number |
| ε | Timescale-separation parameter (Fenichel) |

---

## 16. KEY REFERENCES (BY LAYER)

**A₀:** Gómez et al.; De Domenico et al. (multilayer/supra-Laplacian); Hawkes 1971; Oakes 1975; Daw & Pender 2022; Friston 2010; Ramstead et al. 2019; Biehl, Pollock & Kanai 2021; Aguilera et al. 2022; van der Aalst 2016/2023; Berti, Montali & van der Aalst 2024; Still, Sivak, Bell & Crooks; Holme & Saramäki 2012; Colfer & Baldwin 2016.
**A:** Gunther 2008 (USL); Jones & Tonetti 2020 (non-rivalry); Chen & Mandelbaum 1991; Dai 1995; Kurtz; Carr 1981; Guckenheimer & Holmes 1983; Kuznetsov 2004; Sotomayor; Fenichel 1979; Scheffer et al. 2009; Zahler & Sussmann 1977; Cobb & Grasman; Hawkes & Oakes 1974; Brémaud & Massoulié 1996; Dashkovskiy, Rüffer & Wirth 2010; Feinberg 2019; Anderson & Kurtz 2015; NUREG/CR-5485; Verhulst 1838; Bass 1969; Kephart & White 1991.
**A.5:** Epoch AI; Stanford HAI 2025.
**B:** Damodaran; Crouzet & Ma 2023; OECD TPG Ch. VI; AICPA PPA Guide; Godley & Lavoie; SEEA/SNA 2025; China 2024 data-asset standard; Brummitt (coupled catastrophes); Buldyrev (interdependent percolation).
**Institutional/historical (Paper One):** Barzel; Laney 2018; Coyle; Halley; Huygens; Bernoulli; Lloyd's history.
**Parallel EA Economics track (firewalled, must cite):** Baldwin & Clark, *Design Rules* 2000; Sambamurthy, Bharadwaj & Grover, MISQ 2003.

---

## 17. PUBLICATION STATE (SEPT 2026)

- **Layer A₀ → SSRN**: highest-priority preprint; two tasks gate it (DOI check on ~90 refs, companion-paper edit). Not gated on IP carve-out.
- **Paper One** — "Measurement Infrastructure as the Binding Constraint on Risk-Transfer Market Formation" (~22K words, *Business History Review* target). HELD pending IP carve-out. ~12 Tier C citations remaining; friendly readers Diane Coyle (Cambridge) and Doug Laney.
- **Paper Two** — measurement foundations (proper scoring rules, stack-level risk aggregation). PARKED.
- **Paper Three** — IICB mechanism design. Also the leading Layer C replacement.
- **Layer A layman book** — 7 chapters, ~63 pages, finished.

**Paper One [CONFLICT — unresolved as of 22 Aug 2026]:** the 28 May file says `Paper_One_v1.4_FINAL.docx` ~27.8K words; memory says v1.5 ~22K words regenerated from the v1.4 PDF, Part One only — which may have silently dropped Part Two. Until diffed, assume v1.4_FINAL is the master. Lane 2008 is confirmed dead (drop it); Pearson 2004 is fire-history only (re-attribute marine records to Kingston); Flandreau is 2010 not 2011.

## 18. WHERE THE CANONICAL FILES LIVE (Drive)

- Main Infonomics folder: `1olwhHawZO_c5_ozkgOTqvHgPBatQK1Oy` — subfolders Core, AI insurance, Old, Context Engineering, Self study, and the 22 Aug checkpoint.
- **Start any core session at:** `CHECKPOINT — PICK UP FROM HERE (2026-08-22)` (`1JqI8IEQBAMWvjDY2vp6nCLu1yNNROHE_`): 00 START HERE → 01 AUDIT → 02 MASTER STATE rev 2 → 03 TODO → 04 HANDOVER Spirit → 05 RESEARCH BACKLOG. All native Google Docs.
- Layer A₀ v1.5 Bible: two file IDs are recorded in different places — `1rnM0CAuu4C8cbzokWaziu4v6g_Ej9quy` (Aug checkpoint) and `1mDeyxKdlf-P5idTpIPZuHIopaVN_uek-` (AI-insurance record). Resolve manually; do not assume either.
- Layer A folder: `1c-ejRXBPy1o6B7gqimEaVKe_tnzMbKe_` (layman book backup, 13 files; patched `LayerA_WORKED_BIBLE.md` spine still owed to Drive).
- AI insurance root: `1ok6DWSmbt0EeKQta-WiQdiphwEhNk8Vh`; Paper 2 latest: `1MFGE9AXUMEW37pId_nkh5_pHDAAyqfou`; Paper B explainer canonical: `1Dd6UILKedBpActmB76WjhlccAgRjaSiW`; Measurement-layer folder (Paper 0): `1a2usK31hmMV6A8vhUREGBn2T9rj9Co-K`; onboarding bible (native Doc): `1UV1E8p9KhCIuAx70yl__wViIJgSTDSdsM5TFUnOveak`.
- `/mnt/project/` files are frozen May–June copies; `LayerA0_v1_2_Academic_Paper.md` there is a stale regression.
- Drive connector reads only native Google Docs via read_file_content; `.md` must be pulled via download_file_content + base64 decode.

*End of primer v1.1.*
