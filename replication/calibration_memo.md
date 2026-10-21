# Calibration memo: sourced inputs for the illustrative numerical exercise

*Earn or Terminate? Autonomous Intelligence, Market Selection, and the Macroeconomics of Self-Sustaining Machines*, revision. Prepared 15 October 2026.

Companion files: `calibration_table.csv` (59 sourced rows, including 8 recommended-value rows), `calibration_derivations.py` (reproduces every derived number below), `energy_share_scenarios.csv`, `model_lifecycle_data.csv` (99 model release/retirement records), `derived_values.json`.

## 0. Conventions

**Use labels.**
- *direct*: the source measures the model object, or a close analogue, without transformation.
- *anchor*: the value is sourced, but mapping it to the model requires a transformation or an assumption, or it is derived arithmetic on sourced inputs.
- *illustrative*: the value is chosen for the exercise and is not pinned down by a source.

The paper should call every number illustrative unless a row says *direct*.

**Normalization.** One unit of compute x is normalized so that its replacement cost equals one unit of the final good. Then δ_X is an annual rate, κ_E p_E is the annual energy bill per unit of compute capital, and c = δ_X + κ_E p_E. The energy share is s_E = κ_E p_E / (c + f/x), where f is per-provider fixed overhead (written m in `earn_or_terminate.tex`). Growth rates are continuous log rates, so g = ln(annual factor).

**Provenance.** The table reports only numbers read from retrieved sources or computed from them. When a number came through a secondary source, the `source` column says so.

## 1. Recommended baseline and ranges

| Parameter | Symbol | Baseline | Range | Use | Principal sources |
|---|---|---|---|---|---|
| Compute depreciation / replacement | δ_X | 0.20 /yr | 0.167–0.40 | anchor | Hyperscaler 10-K lives (5–6 yr); Cottier et al. (2024); Hobbhahn et al. (2023); Epoch Trends (2026) |
| Energy share of per-unit cost (f = 0) | s_E | 0.07 | 0.04–0.15 | direct | Michael & Cottier (2026) 0.070; Cottier et al. (2024) 0.09; bottom-up 0.073 |
| Energy cost per unit compute | κ_E p_E | 0.016 /yr | 0.012–0.035 | anchor (derived) | §3 arithmetic |
| Electricity price (input) | p_E | 8.6 ¢/kWh | 8.1–13.9 ¢/kWh | direct | EIA EPM Table 5.3 |
| Power usage effectiveness (input) | PUE | 1.10 | 1.09–1.56 | anchor | Cottier et al.; Google; LBNL via Epoch; Uptime |
| Exogenous provider exit hazard | δ_P | 0.5 /yr | 0.25–1.0 | anchor | Gemini deprecation schedule; Wolfrath et al. (2026) + Epoch release dates |
| Growth of capability per unit compute | g_A | 1.0 /yr (≈2.7×) | 0.6–1.4 | anchor | Ho et al. (2024); Epoch (project CSV); Gundlach et al. (2025) |
| One-time capability shock | Δln a | 1.1 (≈3×) | 0.6–1.4 | anchor | about one year of algorithmic progress |
| Decline of machine-service price (validation target) | g_pM | −1.6 to −2.3 /yr (5–10×) | Epoch median −3.9 as upper bound | anchor | Gundlach et al. (2025); Cottier et al. (2025) |
| Conventional-capital output elasticity | α | 0.38 | 0.32–0.42 (0.475 global) | anchor | PWT 10.01 labor shares |
| Machine–labor elasticity of substitution | σ | regimes 0.6 and 2.0 | 0.3–3.0 | illustrative | No credible direct estimate (§8) |
| Data-centre electricity demand growth (context) | g_E | 12%/yr historical; 14.7%/yr projected | accelerated servers ≈30%/yr | anchor | IEA (2025), via secondary reports |
| AI compute stock growth (context) | g_X | ln 3.4 = 1.22 /yr | 1.16–1.31 (3.2–3.7×) | anchor | Epoch Trends (2026) |

Two of these change the current manuscript's numbers. **First, δ_X.** Revision 2 sets δ_X = 0.12 (range 0.12–0.30), which is below every sourced anchor: even a 6-year accounting life implies 0.167. **Second, the energy cost.** The draft sets κ_E p_E = 0.04 with δ_X = 0.12, which implies s_E = 0.04/0.16 = 0.25. That is roughly three times the published direct estimates (0.07–0.09).

## 2. Compute depreciation δ_X

| Evidence | Value | Implied annual rate |
|---|---|---|
| Microsoft, Alphabet server lives (10-K, via secondary compilations) | 6 yr | 1/6 = 0.167 |
| Meta, most servers and network assets (FY2025 10-K, effective 1 Jan 2025) | 5.5 yr | 0.182 |
| Amazon, subset of servers and networking (from 1 Jan 2025; shortened from 6 yr, citing faster AI/ML technology development) | 5 yr | 0.200 |
| IT lifespan in Epoch's 1-GW data-center TCO model (Michael & Cottier 2026) | 5 yr (facility 14 yr) | 0.200 |
| Cottier et al. (2024): hardware value falls 0.14 OOM/yr (90% CI 0.10–0.18) | 0.14 × ln 10 | 0.322 (0.230–0.415) |
| Hobbhahn, Heim & Aydos (2023): ML-GPU FLOP/$ doubles every 2.1 yr | ln 2 / 2.1 | 0.330 |
| Epoch Trends (2026): AI-chip performance per dollar 1.49×/yr since 2023 (CI 1.36–1.66) | ln 1.49 | 0.399 (0.307–0.507) |

**What the two groups measure.** The 10-K lives measure physical replacement as an accounting estimate. The price-performance rates measure economic obsolescence: the rate at which a fixed-vintage chip loses market value as newer chips get cheaper per FLOP. Cottier et al. judge hardware failures negligible next to obsolescence. They note that the expected lifetime would still be 3.7 years even if every failure were catastrophic.

**Which concept fits the model** depends on how compute is measured.
- If hardware progress enters through capability a (more services per unit of compute) or through the price of new compute, obsolescence is already captured elsewhere, and δ_X should be the physical replacement rate, about 1/5.
- If x is a fixed-vintage physical unit facing ever-better competitors, the economic rate of 0.32–0.40 is the relevant cost.

**Recommendation:** δ_X = 0.20, range 0.167–0.40.

## 3. Energy share s_E

### 3.1 Published direct estimates
- **Michael & Cottier (2026), Epoch AI.** This is a total-cost-of-ownership model of a 1-GW US hyperscaler AI data center. Annualized costs in $ million per year: servers 5,021; facility 1,387; network 1,167; energy 594; taxes 143; maintenance 120; labor 40; utility works 20; land 13; water 6. Capital totals 7,607 and operating costs 907. The energy share is **594 / 8,514 = 0.070**.
  - Model inputs: GB200 NVL72 servers, PUE 1.14 (LBNL), 71% utilization, 8.34 ¢/kWh, and capital annualized with a WACC-based capital-recovery factor.
  - Sensitivity: a 3-year IT life gives 0.046–0.050 (the page reports total annual cost as both $12B and $13B), and a 7-year life gives 0.085.
  - The model's c contains depreciation but no cost of capital. Re-annualizing straight-line (IT 5 yr, facility 14 yr) gives 0.085.
- **Cottier et al. (2024), Sec. 3.4 (p. 7).** Energy averages **9%** of amortized hardware CapEx plus energy for frontier training runs; the rest splits into accelerator chips 44%, other server components 29%, and cluster interconnect 17%. This differs from the paper's 2–6% figure (2–7% excluding equity, Sec. 3.5), which is energy's share of *total* model-development cost including R&D staff. Only the 9% figure is comparable to s_E, because the model's c contains no labor cost.

### 3.2 Bottom-up arithmetic for one H100 GPU (the compute unit)

| Step | Input and source | Result |
|---|---|---|
| Server power per GPU | DGX H100 maximum system power 10.2 kW / 8 GPUs (NVIDIA datasheet, as encoded in Cottier et al.'s replication code); chip TDP 700 W | 1.275 kW |
| Average draw | × 0.75 average power/TDP during training (Cottier et al., App. A.4) | 0.956 kW |
| Facility draw | × PUE 1.10 (hyperscaler; Cottier et al.) | 1.052 kW |
| Annual energy | × 8,760 h | 9,214 kWh |
| Annual energy cost | × $0.0862/kWh (EIA industrial, 2025 annual average) | **$794** |
| Capital per GPU | DGX H100 per-GPU price, median of 5 listings 2022–2025 ($33,750–$46,875), $41,217 × 1.23 cluster-interconnect overhead (Cottier et al.) | $50,697 |
| Annual capital charge | × δ_X = 0.20 | **$10,139** |
| Energy share | 794 / (794 + 10,139) | **s_E = 0.073** |
| Normalized energy cost | 794 / 50,697 | **κ_E p_E = 0.0157** per unit compute per year; κ_E p_E / δ_X = 0.078 |

Scenarios from `energy_share_scenarios.csv`:

| Scenario | δ_X | κ_E p_E | s_E |
|---|---|---|---|
| Baseline (5-yr life, PUE 1.10, industrial 2025) | 0.200 | 0.0157 | 0.073 |
| Baseline + facility capex ($11,433/kW over 14 yr; Michael & Cottier) | 0.200 | 0.0157 | 0.066 |
| Mid (5.5-yr life, PUE 1.14, util. 0.71, 8.34 ¢/kWh) | 0.182 | 0.0149 | 0.076 |
| Low (economic depreciation 0.322) | 0.322 | 0.0157 | 0.046 |
| Low (obsolescence 0.399 + facility capex) | 0.399 | 0.0157 | 0.036 |
| High (6-yr life, PUE 1.25, commercial 13.41 ¢/kWh) | 0.167 | 0.0277 | 0.143 |
| Low energy intensity (PUE 1.09, util. 0.71, industrial 2024, highest DGX price) | 0.200 | 0.0122 | 0.057 |
| High energy intensity (PUE 1.56 Uptime average, commercial 2025) | 0.200 | 0.0346 | 0.147 |
| Extreme (6-yr life, lowest HGX price, PUE 1.56, commercial, full TDP) | 0.167 | 0.0610 | 0.268 |

**Cross-check against rental prices.** Energy costs $0.0907 per GPU-hour. The median on-demand H100 rental in Epoch's price data is $3.47 per GPU-hour (n = 34 listings dated 2024–2025, IQR $2.60–4.29). Energy is therefore 2.6% of the rental price. This is a lower bound, because rental prices include margin, facility costs and staff.

### 3.3 Mapping and recommendation
**s_E = 0.07 at f = 0, range 0.04–0.15.** Three independent routes agree on 0.07–0.09: the published TCO model, the training-cost study, and the bottom-up arithmetic.

**Adding fixed overhead.** With a fixed-overhead share φ_f = (f/x)/(c + f/x), the energy share becomes s_E = 0.07 (1 − φ_f). The TCO model's site-level non-energy operating costs (taxes, maintenance, labor, water) are 313/8,514 = 0.037 of annual cost. This number does not measure the provider-level overhead f, so φ_f remains illustrative.

**Implied energy cost.** At δ_X = 0.20, use κ_E p_E ≈ 0.016, with range 0.012–0.035.

## 4. Exogenous exit hazard δ_P

**Estimator.** λ = D/T, where D is the number of retirements on or before 15 Oct 2026 and T is the model-years at risk, Σ[min(retirement, 15 Oct 2026) − release]. Models with no announced shutdown, or with a future shutdown, are censored. The 90% confidence interval is the exact Poisson (χ²) interval.

| Sample | n | Retired | Exposure (model-yr) | λ (90% CI) | Announced life, mean / median |
|---|---|---|---|---|---|
| Gemini API, all listed models | 83 | 38 | 53.1 | 0.715 (0.54–0.94) | 0.84 / 0.75 yr |
| Gemini API, stable (non-preview) | 39 | 13 | 25.1 | 0.518 (0.31–0.82) | 1.24 / 1.19 yr |
| Gemini API, stable text LLMs | 13 | 4 | 10.7 | 0.375 (0.13–0.86) | 1.23 / 1.26 yr (n = 5) |
| Gemini API, preview | 44 | 25 | 28.0 | 0.892 (0.62–1.25) | 0.66 / 0.59 yr |
| 16 most-used commercial models | 16 | 8 | 33.3 | 0.240 (0.12–0.43); 0.418 if announced retirements count as exits | 2.06 / 1.72 yr (n = 14) |

**Sources for the two samples.**
- *Gemini rows:* release and shutdown dates from Google's "Gemini deprecations" page (last updated 2026-10-12).
- *Commercial-model row:* retirement dates from Wolfrath et al. (2026), Table 1, which compiled them from vendor deprecation pages. Release dates come from the Epoch AI models database. I re-fetched the arXiv PDF of Wolfrath et al. and checked all 16 Table 1 rows used here, plus the 538-day median, against its text. The PDF's SHA-256 checksum is recorded in `source_provenance.csv`.

**Biases.**
- The Gemini page omits earlier retired generations, so its sample is survivorship-selected.
- In the commercial sample, six announced retirements fall within ten weeks of the censoring date, which pulls the MLE down. The most-used models are also probably longer-lived than average.

**Leaderboard turnover.** Unofficial trackers count 19–21 changes of the LMArena #1 position over 39–41 months, a mean tenure of about 2 months. One tracker reports only 2 changes between Aug 2024 and Sep 2026. Because the sources conflict and losing rank is not exit, these counts are context only.

**Mapping caveat.** Deprecation is partly endogenous: a model is retired when a better successor makes it unprofitable. In the model, unprofitable providers already exit through the earn-or-terminate condition, so observed deprecation rates bound the exogenous hazard from above. They are the right object only if each model version is treated as a separate provider.

**Recommendation:** δ_P = 0.5 per year (expected life 2 years), range 0.25–1.0.

## 5. Growth of capability per unit compute, g_A

| Source | Reported | Annual factor | Log rate |
|---|---|---|---|
| Ho et al. (2024), preferred model | effective-compute doubling 8.4 months (95% CI 4.5–14.3) | 2.69× (1.79–6.35) | 0.99 (0.58–1.85) |
| Ho et al. (2024), headline | halving of compute for a fixed threshold, about 8 months (95% CI about 5–14) | 2.83× | 1.04 |
| Epoch AI, pre-training compute efficiency (project CSV) | 3.0×/yr, doubling 7.6 months | 3.0× | 1.10 |
| Gundlach et al. (2025), inference prices hardware-adjusted | about 3×/yr; GPQA-Diamond Pareto 3.72× (90% CI 1.71–8.07) | 3.0×–3.72× | 1.10–1.31 |

**Recommendation:** g_A = 1.0 per year, range 0.6–1.4. For a one-shot capability shock, use Δln a = ln 3 ≈ 1.1, about one year of algorithmic progress.

Two caveats apply.
1. These series measure compute-equivalent efficiency at fixed benchmark performance. They are an upper bound on the growth of economic services per unit of compute.
2. If compute is measured in dollars of hardware rather than FLOP, add hardware price-performance (0.33–0.40 per year), for a total of about 1.4–1.5.

## 6. Decline of the machine-service price, g_pM

- **Cottier, Snodin, Owen & Adamczewski (2025), Epoch AI.** At a fixed capability threshold, LLM inference prices fell by 9× to 900× per year, with a median of 50× per year. In log terms that is −2.2 to −6.8, median −3.9. GPT-4-level GPQA performance fell 40× per year. For trends starting after January 2024 the median is 200× per year.
- **Gundlach et al. (2025).** For frontier (Pareto) models, the price of a given benchmark performance fell 5×–10× per year, or −1.6 to −2.3 in logs. GPQA-Diamond gives 5.3× (90% CI 2.4–11.5) and AIME 11.7× (5.3–25.9). Declines are 31× in the top performance bin and 1.7× in the bottom bin. Meanwhile, the cost of running frontier models rose 3–18× per year.

**Recommendation.** p_M is endogenous, so use these declines as a validation target, not an input: −1.6 to −2.3 per year at the frontier, with the Epoch median of −3.9 as an upper bound.

**Consistency check.** For the cutoff provider, zero operating surplus implies p_M = (c + f/x) / [(1−τ) a*(1−u)]. If c is fixed, p_M falls at the growth rate of a*. Gundlach et al.'s decomposition fits this: roughly 3× from algorithms, times about 1.4–1.5× from hardware, times a residual from margins and competition, gives 5–10×.

## 7. Capital share α

Penn World Table 10.01, variable labsh (R package pwt10 v10.1.0):
- **United States:** 0.597 in 2019, 0.594 average for 2010–2019, 0.632 average for 1970–1979.
- **138 countries, 2019:** median 0.525, GDP-weighted mean 0.547.
- **21 OECD economies, 2019:** median 0.584.

Karabarbounis & Neiman (2014) document a significant decline in the labor share since the early 1980s. Only the abstract was retrieved.

**Linking α to the machine share.** In the model, the labor share is s_L = (1−α)·ψ_L, where ψ_L is labor's share of cognitive income. So 1 − labsh = α + Ω_M, where Ω_M is the initial machine-service share of output. Holding s_L = 0.597:

| Ω_M (illustrative) | α | ψ_L = long-run rebound threshold s_L/(1−α) | short-run threshold ψ_L / [1 − α(1−ψ_L)] |
|---|---|---|---|
| 0 | 0.403 | 1.000 | 1.000 |
| 0.01 | 0.393 | 0.984 | 0.990 |
| 0.02 | 0.383 | 0.968 | 0.980 |
| 0.05 | 0.353 | 0.923 | 0.949 |
| 0.083 | 0.320 | 0.878 | 0.914 |

**Recommendation:** α = 0.38, which corresponds to an illustrative Ω_M = 0.02. Range 0.32–0.42, or 0.475 if calibrating to the global median.

The current α = 0.32 implies Ω_M = 0.083. That is defensible only if M stands for broad ICT and software capital services, not autonomous AI providers alone. No official measure of the AI-services share of output was found, so Ω_M is illustrative.

## 8. Elasticity of substitution σ

**No credible direct estimate exists** of the elasticity between AI or machine services and human labor in aggregate production. The available anchors are:
- **Whitfill & Wu (2025):** research compute versus cognitive labor in four frontier labs, 2014–2024. The CES-in-compute specification gives σ = 2.58; the frontier-experiments specification gives σ = −0.10, i.e. about zero (strong complements). The specifications diverge, and the setting is R&D, not final production.
- **Taniguchi & Yamada (2025, arXiv v9), Table 4:** aggregate Morishima elasticities between ICT capital and labor in OECD data. From labor toward ICT capital: 0.76 (female skilled), 0.99 (male skilled), 1.05 (female unskilled), 1.07 (male unskilled) on the production side, and 0.75–1.67 on the cost side. In the reverse direction the values run from 0.78 to 5.86.
- **Gechert et al. (2022), meta-analysis of capital–labor substitution:** the literature mean is 0.9, falling to 0.3 after correcting for publication bias and method choices.
- **Oberfield & Raval (2021):** 0.5–0.7 for U.S. manufacturing.

**Recommendation.** Keep σ as a regime parameter: σ = 0.6 for complements and σ = 2.0 for substitutes, with a range of 0.3–3.0.

From §7, both rebound ("Jevons") thresholds lie just below one when the initial machine share is small: about 0.92–0.98 long-run and 0.95–0.99 short-run for Ω_M between 0.01 and 0.05. The regime values 0.6 and 2.0 sit on opposite sides of both thresholds. Reporting a pair just below and just above about 0.97 would show the knife-edge.

## 9. Energy context (IEA) and the electricity price path

**IEA (2025), *Energy and AI*, Base Case.** The IEA site returned HTTP 403 to automated retrieval, so these figures come from DatacenterDynamics (2026), NS Energy (2025) and arXiv summaries.
- Data centres used about 415 TWh in 2024, about 1.5% of global electricity.
- Projected use is about 945 TWh in 2030 (about 3%) and about 1,200 TWh in 2035. The implied growth rates are 14.7% per year for 2024–30 and 10.1% per year for 2024–35.
- Use has grown about 12% per year since 2017.
- Electricity use by accelerated servers grows about 30% per year, against about 9% for conventional servers.
- By 2030, US use rises by 240 TWh (+130%) and Chinese use by 175 TWh (+170%).

**Recent electricity prices (EIA, nominal).** The industrial average price rose 6.0% from 2024 to 2025 (8.13 to 8.62 ¢/kWh), and 6.1% on a rolling 12-month basis to July 2026 (8.40 to 8.91). The commercial price rose 5.2% (12.75 to 13.41) and 5.9% (13.08 to 13.85).

**Recommendation.** Hold real p_E constant in the baseline. Use the manuscript's convex energy-ceiling schedule for scarcity scenarios.

**Why energy grows so much more slowly than compute.** Energy demand grows at 12–30% per year while the AI compute stock grows 3.4× per year. The gap is consistent with Epoch's estimate that GPU energy efficiency improves 1.34× per year (log 0.29). If compute is counted in FLOP, κ_E falls at about that rate.

## 10. Verification of the project CSV (`source_reported_ai_scaling.csv`)

| Row | Status on 15 Oct 2026 |
|---|---|
| Notable-model training compute 4.4×/yr (Rahman & Owen 2024) | Confirmed on the Epoch page. The same page also shows 4.7×/yr (90% CI 4.3–5.2) for a regression variant. |
| Frontier-LLM training compute 5×/yr | Confirmed on Epoch Trends (updated 5 Feb 2026); 90% CI 4–6×. |
| AI-chip-stock computing power 3.4×/yr | Confirmed; 90% CI 3.2–3.7×. |
| Pre-training compute efficiency 3.0×/yr | **Not found** in the static HTML of the Trends page fetched today. Re-verify before citing, or cite Ho et al. (2024) instead. |

## 11. Limitations and what was not found

**Secondary sourcing.**
- IEA figures come from secondary reports (HTTP 403).
- The Amazon useful-life change comes from DatacenterDynamics' report of the earnings call and from 10-K text quoted by Behind the Balance Sheet.
- The Microsoft and Alphabet lives come from secondary compilations. The Meta 10-K text was read from the SEC filing as returned by search, because sec.gov could not be fetched directly.
- The H100 TDP and DGX H100 power figures are Epoch's transcriptions of NVIDIA datasheets.
- The Uptime PUE values come from search extracts of Uptime documents.

**Abstract-only sources.** Karabarbounis & Neiman (2014), Gechert et al. (2022), and Oberfield & Raval (2021). The σ > 1 estimate in Karabarbounis & Neiman is known here only qualitatively, from a secondary characterization.

**Small or selected samples for δ_P.** One provider's schedule plus a compiled 16-model table. Hazards are anchors only.

**Not found:**
- A published estimate of σ between AI services and labor in aggregate production.
- An official statistic for the AI-services share of output (Ω_M).
- A primary, consistent dataset on leaderboard tenure.
- A direct retrieval of the IEA report.

## 12. Reproducibility

`calibration_derivations.py` reproduces every derived number in this memo. It reads `model_lifecycle_data.csv` and writes `derived_values.json` and `energy_share_scenarios.csv`. The source records it uses are:
- the Gemini deprecations table, parsed;
- Wolfrath et al. Table 1 matched to Epoch release dates;
- EIA Table 5.3;
- the Epoch training-cost-trends repository, commit 263c40a.

All web sources were accessed 15 October 2026.

`source_provenance.csv` lists every retrieved source with its URL, format and access date, and the items taken from it. For the six arXiv papers it also records page counts and SHA-256 checksums of the PDFs: Wolfrath et al. 2026, Cottier et al. 2024, Ho et al. 2024, Gundlach et al. 2025, Whitfill & Wu 2025, and Taniguchi & Yamada 2025. Each checksum was confirmed identical on a second download. The manifest also marks which sources came through web-search extracts or abstracts only.