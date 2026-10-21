"""Builds calibration_table.csv (columns: parameter, symbol, value, unit, source,
doi_or_url, use, notes). Values are copied from retrieved sources or from
calibration_derivations.py output (derived_values.json, energy_share_scenarios.csv)."""
import csv

COTTIER24 = ("Cottier, Rahman, Fattorini, Maslej, Besiroglu & Owen (2024), 'The rising costs of training "
             "frontier AI models', arXiv:2405.21015")
COTTIER24_URL = "https://arxiv.org/abs/2405.21015 (DOI 10.48550/arXiv.2405.21015)"
MC26 = ("Michael & Cottier (2026), 'Servers account for 60% of the total cost of ownership of a one-gigawatt AI "
        "data center', Epoch AI Data Insight, 14 May 2026")
MC26_URL = "https://epoch.ai/data-insights/ai-datacenter-cost-breakdown"
TCT = ("Epoch AI training-cost-trends repository (code/data for Cottier et al. 2024), commit 263c40a (2026-04-01)")
TCT_URL = "https://github.com/epoch-research/training-cost-trends"
EIA = ("U.S. EIA, Electric Power Monthly, Table 5.3 'Average Price of Electricity to Ultimate Customers: Total by "
       "End-Use Sector, 2016-July 2026' (release 24 Sep 2026)")
EIA_URL = "https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_03"
GEM = "Google AI for Developers, 'Gemini deprecations' (page last updated 2026-10-12); hazard computed in this memo"
GEM_URL = "https://ai.google.dev/gemini-api/docs/deprecations"
WOLF = ("Wolfrath et al. (2026), 'Model Retirement Creates Reproducibility Risk in Biomedical AI Publications', "
        "arXiv:2609.04699, Table 1 (retirement dates) + Epoch AI models database (release dates)")
WOLF_URL = "https://arxiv.org/abs/2609.04699 ; https://epoch.ai/data/all_ai_models.csv"
HO24 = ("Ho, Besiroglu, Erdil, Owen, Rahman, Guo, Atkinson, Thompson & Sevilla (2024), 'Algorithmic progress in "
        "language models', NeurIPS 2024, arXiv:2403.05812")
HO24_URL = "https://arxiv.org/abs/2403.05812 (DOI 10.48550/arXiv.2403.05812)"
GUND = ("Gundlach, Lynch, Mertens & Thompson (2025), 'The Price of Progress: Price Performance and the Future of "
        "AI', arXiv:2511.23455v2")
GUND_URL = "https://arxiv.org/abs/2511.23455 (DOI 10.48550/arXiv.2511.23455)"
EPINF = ("Cottier, Snodin, Owen & Adamczewski (2025), 'LLM inference prices have fallen rapidly but unequally "
         "across tasks', Epoch AI Data Insight, 12 Mar 2025")
EPINF_URL = "https://epoch.ai/data-insights/llm-inference-price-trends"
TRENDS = "Epoch AI (2026), 'Trends in AI' dashboard (updated 5 Feb 2026; fetched 15 Oct 2026)"
TRENDS_URL = "https://epoch.ai/trends"
PWT = ("Feenstra, Inklaar & Timmer (2015), 'The Next Generation of the Penn World Table', AER 105(10):3150-3182; "
       "PWT 10.01 variable labsh via R package pwt10 v10.1.0 (CRAN)")
PWT_URL = "https://doi.org/10.1257/aer.20130954"
IEA = ("IEA (2025), 'Energy and AI' (Base Case); figures as reported by DatacenterDynamics (2026) and NS Energy "
       "(2025); IEA site returned HTTP 403 to automated retrieval")
IEA_URL = ("https://www.iea.org/reports/energy-and-ai ; https://www.datacenterdynamics.com/en/news/"
           "iea-data-center-energy-consumption-set-to-double-by-2030-to-945twh/ ; "
           "https://www.nsenergybusiness.com/analysis/energy-and-ai-key-findings-from-the-iea/")

rows = [
    # ---------------- 1. delta_X ----------------
    ("Server useful life: Meta (most servers and network assets)", "delta_X", "5.5 years (1/5.5 = 0.182 per year)",
     "years", "Meta Platforms Inc., Form 10-K for FY2025 (change in accounting estimate effective 1 Jan 2025)",
     "https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm", "anchor",
     "Accounting estimate, not a physical life; PP&E table still lists servers/network assets at 5-5.5 yrs. "
     "Read from the filing text as returned by web search (sec.gov not directly fetchable)."),
    ("Server useful life: Amazon (subset of servers and networking equipment)", "delta_X",
     "5 years from 1 Jan 2025, shortened from 6 (1/5 = 0.20 per year)", "years",
     "Amazon Q4-2024 earnings call (CFO B. Olsavsky) as reported by DatacenterDynamics, 7 Feb 2025; 10-K wording "
     "quoted by Behind the Balance Sheet (2025)",
     "https://www.datacenterdynamics.com/en/news/amazon-2025-capex-to-reach-100bn-aws-revenue-hit-100bn-in-2024/ ; "
     "https://behindthebalancesheet.substack.com/p/amazons-ai-reality-check", "anchor",
     "Reason given: faster pace of technology development, particularly in AI/ML. Secondary reporting of primary "
     "disclosure. Amazon had extended 5->6 years in 2024."),
    ("Server useful life: Microsoft and Alphabet", "delta_X", "6 years (1/6 = 0.167 per year)", "years",
     "Secondary compilations of 10-K disclosures: l0g.fr, 'How long does an AI server really live?' (2026); GPU "
     "Insights, 'Server useful life: what five 10-Ks disclose' (2026)",
     "https://l0g.fr/en/analysis/how-long-does-ai-server-live/ ; "
     "https://gpuinsights.net/server-useful-life-gpu-depreciation-2026/", "anchor",
     "Microsoft 4->6 yrs from FY2023 (latest 10-K gives a 2-6 yr range); Alphabet servers 4->6 yrs from 2023; "
     "CoreWeave 6 yrs. Primary 10-Ks not fetched."),
    ("Economic depreciation of ML hardware value", "delta_X",
     "0.14 OOM/yr = 0.322 per year continuous (90% CI 0.10-0.18 OOM = 0.230-0.415)", "1/year", COTTIER24 + ", Sec. 2.2 and App. B.3",
     COTTIER24_URL, "anchor",
     "Value falls at the rate of ML-GPU price-performance growth (from Hobbhahn et al. 2023). Hardware failures "
     "judged negligible: expected life >= 3.7 yrs even if all failures were catastrophic (App. A.3)."),
    ("ML GPU price-performance (FLOP per $) doubling time", "delta_X",
     "2.1 years -> ln2/2.1 = 0.330 per year", "years",
     "Hobbhahn, Heim & Aydos (2023), 'Trends in machine learning hardware', Epoch AI, 9 Nov 2023",
     "https://epoch.ai/publications/trends-in-machine-learning-hardware", "anchor",
     "Obsolescence-rate anchor; general GPUs 2.5 yrs. Source of Cottier et al.'s 0.14 OOM/yr."),
    ("AI chip performance per dollar growth since 2023", "delta_X",
     "1.49x/yr (90% CI 1.36-1.66); 0.17 OOM/yr -> ln1.49 = 0.399 per year (CI 0.307-0.507)", "x per year",
     TRENDS, TRENDS_URL, "anchor",
     "Constant 2025 dollars. Gains arrive in spurts (flat to mid-2024, then ~2x as Blackwell became most spending)."),
    ("IT-equipment lifespan used in 1-GW AI data-center TCO model", "delta_X",
     "5 years for IT equipment; 14 years for facility", "years", MC26, MC26_URL, "anchor",
     "Lifespans based on hyperscaler depreciation disclosures; sensitivity 3 and 7 years."),
    # ---------------- 2. energy share ----------------
    ("Energy share of annual total cost of ownership, 1-GW AI data center (published)", "s_E",
     "594 / 8,514 = 0.070", "share of annual cost", MC26, MC26_URL, "direct",
     "Annualized $M/yr: servers 5,021; facility 1,387; network 1,167; energy 594; taxes 143; maintenance 120; labor "
     "40; utility works 20; land 13; water 6 (CapEx 7,607 + OpEx 907). WACC-based capital recovery; GB200 NVL72; "
     "PUE 1.14; utilization 71%; 8.34 c/kWh. IT life 3 yr -> 0.046-0.050; 7 yr -> 0.085; straight-line capital "
     "(this memo) -> 0.085."),
    ("Energy share of amortized hardware CapEx + energy, frontier training runs (published)", "s_E",
     "0.09 (average across frontier models)", "share", COTTIER24 + ", Sec. 3.4", COTTIER24_URL, "direct",
     "Cost basis = amortized hardware CapEx + energy of final training runs (Sec. 3.4, p. 7: chips 44%, rest of server "
     "29%, cluster interconnect 17%, energy 9% on average). Different basis: over full model development incl. R&D "
     "staff, energy is 2-6% (2-7% excluding equity; Sec. 3.5)."),
    ("H100 SXM5 thermal design power", "kappa_E (input)", "700", "W per GPU",
     TCT + ": data/Chip dataset-Grid view.csv (links NVIDIA datasheet)", TCT_URL, "direct", "Chip-level TDP."),
    ("DGX H100 system power per GPU", "kappa_E (input)", "10.2 kW / 8 GPUs = 1.275", "kW per GPU",
     TCT + ": cost_analysis_standalone.py chip_to_server_power(); NVIDIA DGX H100 datasheet (Cottier et al. ref.)",
     TCT_URL, "direct", "Server-level maximum power incl. CPUs, memory, NVSwitch, NICs; secondary transcription of "
     "NVIDIA datasheet."),
    ("Average power draw as share of TDP during training (GPUs)", "kappa_E (input)", "0.75", "ratio",
     COTTIER24 + ", App. A.4", COTTIER24_URL, "anchor",
     "All-things-considered estimate; Michael & Cottier (2026) use 71% utilization."),
    ("Power usage effectiveness: hyperscaler / other data centers", "kappa_E (input)", "1.10 / 1.25", "ratio",
     COTTIER24 + ", App. A.4", COTTIER24_URL, "anchor", "Hyperscaler value based on Patterson et al. (2021) and Meta; "
     "other value from SemiAnalysis."),
    ("Power usage effectiveness: AI-specialized data centers", "kappa_E (input)", "1.14", "ratio",
     MC26 + " (citing Lawrence Berkeley National Laboratory)", MC26_URL, "anchor", "LBNL figure not retrieved directly."),
    ("Power usage effectiveness: Google fleet average 2025", "kappa_E (input)", "1.09", "ratio",
     "Google, 'Power usage effectiveness' (data-center efficiency page)", "https://datacenters.google/efficiency/",
     "direct", "Fleet-wide trailing annual average; includes substations and ancillary buildings."),
    ("Power usage effectiveness: industry average (Uptime Institute survey)", "kappa_E (input)",
     "1.56 (2024 survey, n=526); 1.54 (2025); 1.52 (2026)", "ratio",
     "Uptime Institute Global Data Center Survey 2024; Uptime Intelligence (2026) 'The growing PUE advantage of larger "
     "data centers'; 2025 value as cited by Google efficiency page",
     "https://datacenter.uptimeinstitute.com/rs/711-RIA-145/images/2024.GlobalDataCenterSurvey.Report.pdf ; "
     "https://intelligence.uptimeinstitute.com/resource/growing-pue-advantage-larger-data-centers", "anchor",
     "Upper bound for AI clusters; new large facilities report <= 1.3."),
    ("U.S. average electricity price: industrial sector", "p_E",
     "8.62 (2025 annual); 8.13 (2024); 8.91 (12 months to July 2026)", "US cents per kWh", EIA, EIA_URL, "direct",
     "Note: Epoch training-cost-trends code lists 7.71 c/kWh for 2024 (apparently a partial-year value); EIA annual "
     "figure 8.13 used here."),
    ("U.S. average electricity price: commercial sector", "p_E",
     "13.41 (2025 annual); 12.75 (2024); 13.85 (12 months to July 2026)", "US cents per kWh", EIA, EIA_URL, "direct",
     "Upper end for colocation / smaller sites."),
    ("Data-center-weighted industrial electricity price, 2024", "p_E", "8.34", "US cents per kWh",
     MC26 + " (EIA state industrial prices weighted by Aterio data-center project counts)", MC26_URL, "anchor", ""),
    ("H100 SXM5 purchase price per GPU (8-GPU DGX systems, system price / 8)", "c (capital input)",
     "median 41,217 (n=5: 33,750-46,875; 2022-2025); HGX 8-GPU listings 31,120-37,081", "USD per GPU",
     TCT + ": data/Hardware prices.csv (vendor listings, SemiAnalysis)", TCT_URL, "anchor",
     "Server-level price. Times 1.23 cluster-interconnect overhead (Cottier et al.) = 50,697 USD all-in IT capital "
     "per GPU (this memo)."),
    ("Cluster-level interconnect overhead on server cost", "c (capital input)", "23%", "percent", COTTIER24, COTTIER24_URL,
     "anchor", "From NVIDIA H100 SuperPOD reference architecture (approx. 19-20% of SuperPOD cost)."),
    ("Energy use and cost per H100-year (derived)", "kappa_E, kappa_E*p_E",
     "9,214 kWh/yr; 794 USD/yr; kappa_E*p_E = 0.0157 per USD of IT capital per year", "kWh, USD",
     "This memo: 1.275 kW x 0.75 x PUE 1.10 x 8,760 h x 0.0862 USD/kWh; capital 50,697 USD", "calibration_derivations.py",
     "anchor", "Range of kappa_E*p_E across scenarios: 0.012 (PUE 1.09, util 0.71, 2024 industrial price, highest DGX price) to 0.035 (PUE 1.56, commercial price); 0.061 extreme (HGX price, full TDP)."),
    ("Energy share, bottom-up H100 arithmetic (derived)", "s_E",
     "0.073 baseline; 0.036-0.147 across scenarios; 0.268 extreme", "share",
     "This memo (inputs: rows above; delta_X = 0.20)", "energy_share_scenarios.csv", "anchor",
     "s_E = E/(E + delta_X*K). With facility capex 0.066; with 0.322/yr economic depreciation 0.046; 6-yr life, PUE "
     "1.25, commercial price 0.143."),
    ("Energy share of H100 cloud rental price (cross-check)", "s_E", "0.026", "share",
     "This memo: 0.0907 USD/GPU-h energy vs. median on-demand 3.47 USD/GPU-h (n=34 listings dated 2024-2025, IQR "
     "2.60-4.29) from Epoch hardware price data", TCT_URL, "anchor",
     "Lower bound: rental price includes margin, facility, staff."),
    ("GPU energy efficiency (FLOP/s per watt) growth since 2008", "kappa_E (dynamics)",
     "1.34x per year (90% CI 1.29-1.39); doubling 2.4 years; log rate 0.29", "x per year", TRENDS, TRENDS_URL, "anchor",
     "If compute is measured in FLOP, energy per unit compute kappa_E falls at about 0.29/yr; if measured per GPU, kappa_E is roughly constant."),
    ("Non-energy operating overhead share of annual TCO (site level)", "f/x (context)", "313 / 8,514 = 0.037", "share",
     MC26, MC26_URL, "anchor",
     "Taxes, maintenance, labor, water. Provider-level fixed overhead f in the model is not measured by this."),
    # ---------------- 3. delta_P ----------------
    ("Exit hazard: Gemini API stable (non-preview) models", "delta_P",
     "0.52 per year (90% CI 0.31-0.82); 13 shutdowns / 25.1 model-years; mean announced life 1.24 yr (n=16)",
     "1/year", GEM, GEM_URL, "anchor",
     "Exponential MLE; models without announced shutdown censored at 15 Oct 2026. Page omits older retired generations "
     "(e.g. Gemini 1.x), so sample is survivorship-selected."),
    ("Exit hazard: Gemini API stable text LLMs", "delta_P",
     "0.375 per year (90% CI 0.13-0.86); 4 shutdowns / 10.7 model-years; announced lives 1.0-1.32 yr (n=5)", "1/year",
     GEM, GEM_URL, "anchor", "Small sample."),
    ("Exit hazard: Gemini API preview models", "delta_P",
     "0.89 per year (90% CI 0.62-1.25); mean announced life 0.66 yr (n=35)", "1/year", GEM, GEM_URL, "anchor",
     "Upper anchor: previews are designed to be short-lived."),
    ("Exit hazard: 16 most-used commercial models (OpenAI, Anthropic, Google, xAI)", "delta_P",
     "MLE 0.24 per year (90% CI 0.12-0.43; 8 retirements / 33.3 model-years); 0.42 per year if announced retirements "
     "count as exits; release-to-retirement mean 2.06 yr, median 1.72 yr (n=14)", "1/year", WOLF, WOLF_URL, "anchor",
     "Retirement dates from vendor deprecation pages as compiled by Wolfrath et al.; six retirements fall within 10 "
     "weeks of the censoring date. Popular models are likely longer-lived than average."),
    ("Publication-to-retirement interval for models used in biomedical papers", "delta_P (context)",
     "median 538 days; mean 546 days", "days", WOLF, "https://arxiv.org/abs/2609.04699", "anchor",
     "Measures time from paper publication, not model release."),
    ("Leaderboard turnover (LMArena / Chatbot Arena #1)", "delta_P (context)",
     "19-21 lead changes over 39-41 months (mean tenure at #1 about 1.9-2 months); one tracker reports only 2 changes "
     "Aug 2024-Sep 2026", "count",
     "Unofficial trackers: AceCamp (2026) 'Do LLMs truly have moats?'; BenchLM (2026) leaderboard history and market "
     "statistics", "https://acecampai.substack.com/p/do-llms-truly-have-moats ; https://benchlm.ai/llm-leaderboard-history ; "
     "https://benchlm.ai/stats/llm-market", "anchor",
     "Context only: sources conflict and are non-authoritative; losing rank is not exit. Not used to set delta_P."),
    # ---------------- 4. growth of A ----------------
    ("Algorithmic progress in LM pre-training (compute-equivalent)", "g_A",
     "halving time 8.4 months (95% CI 4.5-14.3) -> 2.69x/yr; log rate 0.99/yr (0.58-1.85)", "1/year", HO24, HO24_URL,
     "anchor", "Headline: ~8 months (95% CI ~5-14). Measures compute needed for fixed perplexity, not economic "
     "service value."),
    ("Pre-training compute efficiency (project CSV)", "g_A", "3.0x/yr (doubling 7.6 months) -> log rate 1.10/yr",
     "x per year", "Epoch AI (2026) as recorded in source_reported_ai_scaling.csv", TRENDS_URL, "anchor",
     "Not present in the static HTML of the Trends page fetched 15 Oct 2026; re-verify before citing. Consistent with "
     "Ho et al. and Gundlach et al."),
    ("Algorithmic efficiency inferred from inference prices (hardware-adjusted)", "g_A",
     "~3x/yr; GPQA-Diamond Pareto (all licenses) 3.72x/yr (90% CI 1.71-8.07)", "x per year", GUND, GUND_URL, "anchor",
     "Open-weight models used to control for competition; divided by hardware price declines."),
    # ---------------- 5. fall in p_M ----------------
    ("LLM inference price decline at fixed capability", "g_pM",
     "9x-900x per year across benchmarks/thresholds; median 50x/yr; GPT-4-level GPQA 40x/yr; median 200x/yr for "
     "trends starting after Jan 2024", "x per year", EPINF, EPINF_URL, "anchor",
     "Log change: -2.2 (9x) to -6.8 (900x); median -3.9 per year. Prices per token, cheapest model above threshold."),
    ("Price of a given benchmark performance, frontier (Pareto) models", "g_pM",
     "5x-10x per year (GPQA-Diamond 5.3x, 90% CI 2.4-11.5; AIME 11.7x, CI 5.3-25.9); top-performance bin ~31x, lowest "
     "1.7x; cost of running frontier models rising 3-18x/yr", "x per year", GUND, GUND_URL, "anchor",
     "Log change -1.6 to -2.3 per year. Preferred target because it conditions on frontier performance."),
    # ---------------- 6. alpha ----------------
    ("Labor share of GDP, United States 2019 (PWT 10.01)", "alpha (via 1 - labsh)",
     "labsh 0.597 -> 1 - labsh = 0.403; 2010-2019 mean labsh 0.594; 1970-1979 mean 0.632", "share", PWT, PWT_URL,
     "direct", "1 - labsh = alpha + machine-service share Omega_M in the model (s_L = labsh)."),
    ("Labor share of GDP, cross-country 2019 (PWT 10.01)", "alpha (via 1 - labsh)",
     "median 0.525 (n=138); rgdpna-weighted mean 0.547; 21 OECD economies median 0.584 (min 0.317, max 0.684)",
     "share", PWT, PWT_URL, "direct", "Upper anchor for alpha (0.475 at global median)."),
    ("Decline of the global labor share", "alpha (context)",
     "significant decline since early 1980s within most countries and industries; cheaper investment goods explain "
     "about half", "qualitative", "Karabarbounis & Neiman (2014), 'The Global Decline of the Labor Share', QJE "
     "129(1):61-103", "https://doi.org/10.1093/qje/qjt032", "anchor", "Only the abstract was retrieved."),
    # ---------------- 7. sigma ----------------
    ("Elasticity of substitution: research compute vs cognitive labor in frontier AI labs", "sigma",
     "2.58 (CES-in-compute) vs -0.10 (frontier-experiments; ~0, strong complements)", "elasticity",
     "Whitfill & Wu (2025), 'Will Compute Bottlenecks Prevent an Intelligence Explosion?', arXiv:2507.23181",
     "https://arxiv.org/abs/2507.23181 (DOI 10.48550/arXiv.2507.23181)", "anchor",
     "R&D production (4 labs, 2014-2024), not final-production AI services vs labor; specifications diverge."),
    ("Aggregate (Morishima) elasticities: ICT capital vs labor types, OECD", "sigma",
     "eps(labor,ICT): 0.76 female skilled, 0.99 male skilled, 1.05 female unskilled, 1.07 male unskilled "
     "(production); 0.75-1.67 (cost); reverse direction 0.78-5.86", "elasticity",
     "Taniguchi & Yamada (2025), 'The Race between Technology and Woman', arXiv:2005.12600v9, Table 4",
     "https://arxiv.org/abs/2005.12600 (DOI 10.48550/arXiv.2005.12600)", "anchor",
     "ICT capital (computers/communication) is a proxy for machine services; Morishima elasticities are asymmetric."),
    ("Capital-labor elasticity: meta-analysis", "sigma",
     "literature mean 0.9; 0.3 after correcting for publication bias and method choices (3,186 estimates, 121 studies)",
     "elasticity", "Gechert, Havranek, Irsova & Kolcunova (2022), RED 45:55-82",
     "https://doi.org/10.1016/j.red.2021.05.003", "anchor", "Aggregate capital, not AI; abstract retrieved."),
    ("Aggregate capital-labor elasticity, U.S. manufacturing", "sigma", "0.5-0.7", "elasticity",
     "Oberfield & Raval (2021), 'Micro Data and Macro Technology', Econometrica 89(2):703-732",
     "https://doi.org/10.3982/ECTA12807", "anchor", "Abstract retrieved."),
    # ---------------- 8. energy demand context ----------------
    ("Global data-centre electricity consumption, 2024", "g_E (context)", "about 415 TWh (about 1.5% of global electricity)",
     "TWh", IEA, IEA_URL, "anchor", "US 45%, China 25%, Europe 15% of 2024 consumption."),
    ("Projected data-centre electricity consumption, 2030 and 2035 (Base Case)", "g_E (context)",
     "about 945 TWh in 2030 (about 3% of global); about 1,200 TWh in 2035; implied CAGR 14.7% (2024-30), 10.1% (2024-35)",
     "TWh", IEA + "; 3% share from Nature-portfolio article 'Artificial intelligence data centers could reach one percent of global electricity demand by 2030' (2026); 2035 value as in arXiv:2605.18935", IEA_URL + " ; https://www.nature.com/articles/s44458-026-00152-5 ; https://arxiv.org/abs/2605.18935", "anchor",
     "US +240 TWh (+130%), China +175 TWh (+170%) by 2030. AI-optimised data-centre demand more than quadruples."),
    ("Historical growth of data-centre electricity consumption", "g_E (context)", "about 12% per year since 2017",
     "percent per year", IEA, IEA_URL, "anchor", "More than four times total electricity-consumption growth."),
    ("Electricity use of accelerated servers (Base Case)", "g_E (context)",
     "about 30% per year (conventional servers about 9%)", "percent per year",
     IEA + "; as summarized in arXiv:2606.21064", IEA_URL + " ; https://arxiv.org/abs/2606.21064", "anchor", ""),
    # ---------------- compute scaling (project CSV, re-checked) ----------------
    ("Training compute of notable AI models since 2010", "g_X (context)", "4.4x per year", "x per year",
     "Rahman & Owen (2024), Epoch AI Data Insight", "https://epoch.ai/data-insights/compute-trend-post-2010", "anchor",
     "Re-checked 15 Oct 2026 (page also shows 4.7x/yr, 90% CI 4.3-5.2, for a regression variant)."),
    ("Frontier-LLM training compute since 2020", "g_X (context)", "5x per year (90% CI 4-6x); doubling 5.2 months",
     "x per year", TRENDS, TRENDS_URL, "anchor", "Re-checked 15 Oct 2026."),
    ("Computing power of the AI-chip stock", "g_X (context)", "3.4x per year (90% CI 3.2-3.7x); doubling 6.8 months; log rate 1.22",
     "x per year", TRENDS, TRENDS_URL, "anchor", "Re-checked 15 Oct 2026; since 2022."),
    # ---------------- recommended values ----------------
    ("RECOMMENDED: compute depreciation / replacement rate", "delta_X", "baseline 0.20; range 0.167-0.40", "1/year",
     "This memo, from 10-K useful lives (5-6 yrs) and Epoch/Cottier obsolescence rates", "calibration_memo.md",
     "anchor", "Current manuscript baseline 0.12 is below every sourced anchor."),
    ("RECOMMENDED: energy share of per-unit operating cost (f = 0)", "s_E", "baseline 0.07; range 0.04-0.15",
     "share", "This memo, from Michael & Cottier (2026), Cottier et al. (2024), bottom-up H100 arithmetic",
     "calibration_memo.md", "direct",
     "With fixed-overhead share phi_f: s_E = 0.07(1 - phi_f). Draft values kappa_E*p_E = 0.04 with delta_X = 0.12 "
     "imply s_E = 0.25."),
    ("RECOMMENDED: energy cost per unit compute (compute unit price = 1)", "kappa_E*p_E",
     "baseline 0.016; range 0.012-0.035", "per unit compute per year", "This memo (bottom-up arithmetic)",
     "calibration_memo.md", "anchor", "Implied kappa_E*p_E/delta_X = 0.08 at baseline."),
    ("RECOMMENDED: exogenous provider exit hazard", "delta_P", "baseline 0.5; range 0.25-1.0", "1/year",
     "This memo, from Gemini deprecation schedule and flagship-model retirements", "calibration_memo.md", "anchor",
     "Deprecations are partly endogenous obsolescence, so these rates bound the exogenous hazard from above."),
    ("RECOMMENDED: growth of capability per unit compute", "g_A",
     "baseline 1.0 per year (about 2.7x); range 0.6-1.4; one-shot capability shock dln(a) = ln 3 = 1.1", "1/year",
     "This memo, from Ho et al. (2024), Epoch (CSV), Gundlach et al. (2025)", "calibration_memo.md", "anchor",
     "Effective-compute growth is an upper bound for growth of economic services per unit compute."),
    ("RECOMMENDED: target decline of machine-service price", "g_pM",
     "-1.6 to -2.3 log points per year (5-10x); Epoch median -3.9 as upper bound", "1/year",
     "This memo, from Gundlach et al. (2025) and Cottier et al. (2025)", "calibration_memo.md", "anchor",
     "p_M is endogenous: use as validation moment, not as an input."),
    ("RECOMMENDED: conventional-capital output elasticity", "alpha",
     "baseline 0.38; range 0.32-0.42 (0.475 global)", "share",
     "This memo: alpha = 1 - s_L - Omega_M with s_L = 0.597 (PWT US 2019) and illustrative Omega_M in [0, 0.083]",
     "calibration_memo.md", "anchor",
     "alpha = 0.32 (current manuscript) implies an initial machine-service share Omega_M = 0.083 of output."),
    ("RECOMMENDED: elasticity of substitution between machine services and labor", "sigma",
     "regime values 0.6 and 2.0; range 0.3-3.0; rebound thresholds near 0.92-0.99", "elasticity",
     "This memo: no credible direct estimate exists; anchors above", "calibration_memo.md", "illustrative",
     "Long-run threshold sigma* = s_L/(1-alpha) = 0.968 at alpha = 0.383; short-run 0.980."),
]

with open("calibration_table.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["parameter", "symbol", "value", "unit", "source", "doi_or_url", "use", "notes"])
    w.writerows(rows)
print(len(rows), "rows written")