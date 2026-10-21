"""Derived calibration values for the illustrative numerical exercise in
'Earn or Terminate? Autonomous Intelligence, Market Selection, and the
Macroeconomics of Self-Sustaining Machines'.

Every input constant below is copied from a retrieved source (cited inline);
all outputs are arithmetic on those inputs. Requires numpy, pandas, scipy.
Inputs: model_lifecycle_data.csv (same folder). Outputs: derived_values.json,
energy_share_scenarios.csv.
"""
import json
import math

import numpy as np
import pandas as pd
from scipy.stats import chi2

HOURS = 8760
EVAL_DATE = pd.Timestamp("2026-10-15")  # censoring date for hazard estimates

# ---------------------------------------------------------------------------
# 1. Depreciation of compute capital (delta_X)
# ---------------------------------------------------------------------------
useful_life_years = {
    "Microsoft/Alphabet servers (10-K, via secondary compilation)": 6.0,
    "Meta most servers and network assets (FY2025 10-K)": 5.5,
    "Amazon subset of servers and networking (from 2025)": 5.0,
    "Epoch 1-GW TCO model IT equipment (Michael & Cottier 2026)": 5.0,
}
delta_from_life = {k: 1.0 / v for k, v in useful_life_years.items()}
# Economic (obsolescence) depreciation
cottier_ooms = 0.14            # Cottier et al. (2024), Sec. 2.2: 0.14 OOM/yr (90% CI 0.10-0.18)
cottier_ci_ooms = (0.10, 0.18)
hobbhahn_doubling_yrs = 2.1    # Hobbhahn, Heim & Aydos (2023): ML GPU FLOP/$ doubling time
epoch_perf_per_dollar = 1.49   # Epoch AI Trends (updated 2026-02-05): AI chip perf/$ x/yr since 2023
epoch_perf_per_dollar_ci = (1.36, 1.66)
delta_econ = {
    "Cottier et al. 2024 (0.14 OOM/yr)": cottier_ooms * math.log(10),
    "Cottier et al. 2024 CI low (0.10 OOM/yr)": cottier_ci_ooms[0] * math.log(10),
    "Cottier et al. 2024 CI high (0.18 OOM/yr)": cottier_ci_ooms[1] * math.log(10),
    "Hobbhahn et al. 2023 (FLOP/$ doubling 2.1 yr)": math.log(2) / hobbhahn_doubling_yrs,
    "Epoch Trends 2026 (perf/$ 1.49x/yr)": math.log(epoch_perf_per_dollar),
    "Epoch Trends 2026 CI low (1.36x/yr)": math.log(epoch_perf_per_dollar_ci[0]),
    "Epoch Trends 2026 CI high (1.66x/yr)": math.log(epoch_perf_per_dollar_ci[1]),
}

# ---------------------------------------------------------------------------
# 2. Bottom-up energy share of the annual cost of one unit of AI compute (s_E)
# ---------------------------------------------------------------------------
P_SERVER_KW_PER_GPU = 10.2 / 8   # DGX H100 max system power 10.2 kW / 8 GPUs (NVIDIA datasheet,
                                 # as encoded in Cottier et al. 2024 replication code)
H100_TDP_KW = 0.700              # H100 SXM5 TDP (Epoch ML hardware data; NVIDIA datasheet)
UTIL_TRAINING = 0.75             # avg power / TDP during training, GPUs (Cottier et al. 2024, App. A.4)
UTIL_TCO = 0.71                  # utilization in Michael & Cottier (2026)
PUE = {"hyperscaler (Cottier)": 1.10, "AI-specialized DC (LBNL via Michael & Cottier)": 1.14,
       "non-hyperscaler (Cottier)": 1.25, "Uptime industry average 2024": 1.56}
PRICE_USD_KWH = {"EIA industrial 2025": 0.0862, "EIA industrial 2024": 0.0813,
                 "EIA commercial 2025": 0.1341, "DC-weighted industrial 2024 (Michael & Cottier)": 0.0834}
DGX_H100_PER_GPU_USD = [44489.88, 33750.00, 41197.50, 41217.00, 46875.00]  # Epoch hardware price data
HGX_H100_MIN_PER_GPU_USD = 31119.50                                          # Epoch hardware price data
NETWORK_OVERHEAD = 1.23          # cluster-level interconnect overhead (Cottier et al. 2024)
FACILITY_CAPEX_PER_KW = 11433.0  # $/kW IT: facility capex $11,433M per GW (Michael & Cottier 2026)
FACILITY_LIFE = 14.0             # years (Michael & Cottier 2026)

cap_gpu = float(np.median(DGX_H100_PER_GPU_USD))
facility_per_kw_yr = FACILITY_CAPEX_PER_KW / FACILITY_LIFE


def scenario(name, delta, cap_per_gpu, util, pue, price, facility=0.0):
    kwh = P_SERVER_KW_PER_GPU * util * pue * HOURS
    energy = kwh * price
    capital_all_in = cap_per_gpu * NETWORK_OVERHEAD
    capital_charge = delta * capital_all_in + facility * P_SERVER_KW_PER_GPU
    return {
        "scenario": name, "delta_X": round(delta, 4), "capital_per_GPU_usd": round(capital_all_in),
        "utilization": util, "PUE": pue, "p_E_usd_per_kWh": price, "kWh_per_GPU_year": round(kwh),
        "energy_usd_per_GPU_year": round(energy), "capital_charge_usd_per_GPU_year": round(capital_charge),
        "kappaE_pE_per_usd_capital": round(energy / capital_all_in, 4),
        "s_E": round(energy / (energy + capital_charge), 4),
    }


scenarios = pd.DataFrame([
    scenario("Baseline: 5-yr life, PUE 1.10, EIA industrial 2025", 0.20, cap_gpu, UTIL_TRAINING, 1.10, 0.0862),
    scenario("Baseline + facility capex (14-yr life)", 0.20, cap_gpu, UTIL_TRAINING, 1.10, 0.0862, facility_per_kw_yr),
    scenario("Mid: 5.5-yr life, PUE 1.14, util 0.71, DC-weighted 2024 price", 1 / 5.5, cap_gpu, UTIL_TCO, 1.14, 0.0834),
    scenario("Low: economic depreciation 0.322/yr", 0.14 * math.log(10), cap_gpu, UTIL_TRAINING, 1.10, 0.0862),
    scenario("Low: obsolescence 0.399/yr + facility capex", math.log(1.49), cap_gpu, UTIL_TRAINING, 1.10, 0.0862,
             facility_per_kw_yr),
    scenario("High: 6-yr life, PUE 1.25, EIA commercial 2025", 1 / 6, cap_gpu, UTIL_TRAINING, 1.25, 0.1341),
    scenario("Low energy intensity: PUE 1.09, util 0.71, EIA industrial 2024, max DGX price", 0.20,
             max(DGX_H100_PER_GPU_USD), UTIL_TCO, 1.09, 0.0813),
    scenario("High energy intensity: PUE 1.56 (Uptime avg), util 0.75, EIA commercial 2025", 0.20, cap_gpu,
             UTIL_TRAINING, 1.56, 0.1341),
    scenario("Extreme: 6-yr life, HGX price, PUE 1.56, commercial, full TDP", 1 / 6, HGX_H100_MIN_PER_GPU_USD, 1.00,
             1.56, 0.1341),
])

# Published TCO decomposition (Michael & Cottier 2026), $ million per year, 1-GW AI data center
tco_annual = {"servers": 5021, "facility": 1387, "network": 1167, "energy": 594, "taxes": 143,
              "maintenance": 120, "labor": 40, "utility_works": 20, "land": 13, "water": 6}
tco_capex_total, tco_opex_total = 7607, 907
tco_total = tco_capex_total + tco_opex_total
upfront_capex = {"servers": 21188, "facility": 11433, "network": 4925, "land": 172, "utility_works": 164}
s_E_tco = tco_annual["energy"] / tco_total
straight_line_capital = (upfront_capex["servers"] / 5 + upfront_capex["network"] / 5
                         + upfront_capex["facility"] / FACILITY_LIFE + tco_annual["utility_works"])
s_E_tco_straight_line = tco_annual["energy"] / (straight_line_capital + tco_opex_total)
s_E_tco_it_life = {"3-yr IT life (total $12B)": 594 / 12000, "3-yr IT life (total $13B)": 594 / 13000,
                   "7-yr IT life (total $7B)": 594 / 7000}
non_energy_opex_share = (tco_opex_total - tco_annual["energy"]) / tco_total

# Rental cross-check (Epoch hardware price data, H100 on-demand listings dated 2024-2025)
H100_ONDEMAND_MEDIAN = 3.47      # $/GPU-hour, n = 34 listings (IQR 2.60-4.29)
energy_per_gpu_hour = P_SERVER_KW_PER_GPU * UTIL_TRAINING * 1.10 * 0.0862
s_E_rental = energy_per_gpu_hour / H100_ONDEMAND_MEDIAN

# ---------------------------------------------------------------------------
# 3. Exit hazard of deployed models (delta_P)
# ---------------------------------------------------------------------------
lc = pd.read_csv("model_lifecycle_data.csv", parse_dates=["release", "retirement"])
lc = lc[lc["release"].notna()].copy()


def hazard(df):
    event = df["retirement"].notna() & (df["retirement"] <= EVAL_DATE)
    end = df["retirement"].where(event, EVAL_DATE)
    exposure = ((end - df["release"]).dt.days.clip(lower=0) / 365.25).sum()
    d = int(event.sum())
    lam = d / exposure
    lo = chi2.ppf(0.05, 2 * d) / (2 * exposure) if d > 0 else 0.0
    hi = chi2.ppf(0.95, 2 * (d + 1)) / (2 * exposure)
    sched = ((df["retirement"] - df["release"]).dt.days / 365.25).dropna()
    # hazard treating announced (future) retirements as realised exits
    exp_sched = sched.sum() + ((EVAL_DATE - df.loc[df["retirement"].isna(), "release"]).dt.days / 365.25).sum()
    return {"n_models": int(len(df)), "retired_by_eval_date": d, "exposure_model_years": round(exposure, 2),
            "hazard_mle_per_year": round(lam, 3), "hazard_90ci": [round(lo, 3), round(hi, 3)],
            "n_with_announced_retirement": int(len(sched)),
            "scheduled_life_mean_years": round(float(sched.mean()), 2) if len(sched) else None,
            "scheduled_life_median_years": round(float(sched.median()), 2) if len(sched) else None,
            "hazard_incl_announced_retirements": round(len(sched) / exp_sched, 3) if len(sched) else None}


gem = lc[lc["dataset"].str.startswith("Gemini")]
flag = lc[lc["dataset"].str.startswith("Flagship")]
hazards = {
    "Gemini: all listed models": hazard(gem),
    "Gemini: stable (non-preview)": hazard(gem[~gem["preview"]]),
    "Gemini: preview": hazard(gem[gem["preview"]]),
    "Gemini: stable text LLMs": hazard(gem[gem["llm"] & ~gem["preview"]]),
    "Flagship commercial models (Wolfrath + Epoch)": hazard(flag),
}

# ---------------------------------------------------------------------------
# 4. Growth of capability per unit compute (g_A) and fall in p_M
# ---------------------------------------------------------------------------
def from_doubling_months(m):
    return {"annual_factor": round(2 ** (12 / m), 2), "log_rate": round(math.log(2) * 12 / m, 3)}


growth = {
    "Ho et al. 2024 central (8.4 months)": from_doubling_months(8.4),
    "Ho et al. 2024 headline (8 months)": from_doubling_months(8.0),
    "Ho et al. 2024 95% CI slow (14.3 months)": from_doubling_months(14.3),
    "Ho et al. 2024 95% CI fast (4.5 months)": from_doubling_months(4.5),
    "Epoch pre-training compute efficiency (3.0x/yr, project CSV)": {"annual_factor": 3.0, "log_rate": round(math.log(3.0), 3)},
    "Gundlach et al. 2025 hardware-adjusted (~3x/yr)": {"annual_factor": 3.0, "log_rate": round(math.log(3.0), 3)},
    "Gundlach et al. 2025 GPQA Pareto hardware-adjusted 3.72x": {"annual_factor": 3.72, "log_rate": round(math.log(3.72), 3)},
}
price_decline = {k: round(-math.log(v), 3) for k, v in {
    "Gundlach 5x/yr": 5.0, "Gundlach 10x/yr": 10.0, "Epoch 9x/yr (slowest)": 9.0,
    "Epoch median 50x/yr": 50.0, "Epoch post-2024 median 200x/yr": 200.0, "Epoch 900x/yr (fastest)": 900.0}.items()}

# ---------------------------------------------------------------------------
# 5. Capital share alpha and the implied rebound ('Jevons') thresholds
# ---------------------------------------------------------------------------
S_L_US_2019 = 0.5970911          # PWT 10.01 labsh, USA 2019 (pwt10 R package v10.1.0)
alpha_thresholds = {}
for omega_m in (0.0, 0.01, 0.02, 0.05, 0.083):   # illustrative initial machine-service share of output
    alpha = 1 - S_L_US_2019 - omega_m
    psi_L = S_L_US_2019 / (1 - alpha)            # labor share of cognitive income
    alpha_thresholds[f"Omega_M={omega_m}"] = {
        "alpha": round(alpha, 3), "psi_L": round(psi_L, 4),
        "long_run_sigma_threshold": round(psi_L, 4),
        "short_run_sigma_threshold": round(psi_L / (1 - alpha * (1 - psi_L)), 4)}

out = {
    "delta_from_useful_life": {k: round(v, 4) for k, v in delta_from_life.items()},
    "delta_economic": {k: round(v, 4) for k, v in delta_econ.items()},
    "capital_per_GPU_median_DGX_usd": cap_gpu,
    "s_E_tco_published": round(s_E_tco, 4),
    "s_E_tco_straight_line": round(s_E_tco_straight_line, 4),
    "s_E_tco_it_life_sensitivity": {k: round(v, 4) for k, v in s_E_tco_it_life.items()},
    "non_energy_opex_share_of_tco": round(non_energy_opex_share, 4),
    "energy_cost_per_gpu_hour_usd": round(energy_per_gpu_hour, 4),
    "s_E_rental_crosscheck": round(s_E_rental, 4),
    "hazards": hazards,
    "growth_A": growth,
    "log_change_pM_per_year": price_decline,
    "alpha_and_rebound_thresholds": alpha_thresholds,
    "iea_cagr_2024_2030": round((945 / 415) ** (1 / 6) - 1, 4),
    "iea_cagr_2024_2035": round((1200 / 415) ** (1 / 11) - 1, 4),
    "compute_stock_log_growth": round(math.log(3.4), 3),
}
scenarios.to_csv("energy_share_scenarios.csv", index=False)
with open("derived_values.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
print(scenarios.to_string())
print(json.dumps(out, indent=2))