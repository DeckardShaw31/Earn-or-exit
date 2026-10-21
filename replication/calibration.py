"""
calibration.py -- baseline parameters for the illustrative quantitative exercise.

Sources and use labels (see calibration_table.csv / calibration_memo.md):
  alpha   = 0.38   anchor   PWT 10.01 US labor share 0.597 with an illustrative machine-service share Omega_M = 0.02
  Omega_M = 0.02   illust.  initial machine-service share of output (no official statistic exists)
  delta_X = 0.20   anchor   5-6 year accelerator/server useful lives (hyperscaler 10-Ks; Michael & Cottier 2026)
  kE_pE   = 0.016  anchor   bottom-up H100 arithmetic; energy share s_E = 0.074 (direct estimates 0.07-0.09)
  f       = 0      illust.  provider-level fixed overhead (not separately measured)
  deltaP  = 0.5    anchor   model-retirement hazards (Gemini deprecation schedule; Wolfrath et al. 2026)
  r       = 0.04   illust.  discount rate
  deltaK  = 0.06   illust.  depreciation of conventional capital (enters only through y_K)
  theta   = 3      illust.  Pareto shape of the capability distribution of entrants
  fail    = 0.5    illust.  share of entrants that never operate in the stationary equilibrium (pins f_e)
  Delta   = ln 3   anchor   one-time capability shock ~ one year of algorithmic progress (Ho et al. 2024)
  g_A     = 1.0    anchor   growth of capability per unit of compute (log rate per year)

Normalization (normalized CES): z0 = M0/L0 = 1 and omega = psi_L0 = 1 - Omega_M/(1-alpha), so that the
initial labor share of cognitive income is the same for every sigma and sigma only changes curvature.
K0 is set so that Y0/K0 = y_K: the initial state is simultaneously the short-run (K fixed) and the
long-run (capital adjusted) stationary equilibrium.  A0 is set so that the free-entry break-even price
equals the initial marginal product of machine services.
"""
import numpy as np
import eot_model as em

CAL = dict(alpha=0.38, Omega_M=0.02, delta_X=0.20, kE_pE=0.016, f=0.0, deltaP=0.5, r=0.04,
           deltaK=0.06, theta=3.0, fail=0.5, Delta=np.log(3.0), g_A=1.0, x=1.0, u=0.0, tau=0.0)


def build(sigma, cal=None, **over):
    """Parameter dict for eot_model at the calibrated initial stationary equilibrium."""
    c = dict(CAL)
    if cal is not None:
        c.update(cal)
    c.update(over)
    al = c['alpha']
    psiM0 = c['Omega_M'] / (1 - al)
    omega = 1 - psiM0
    yK = (c['r'] + c['deltaK']) / al
    Phi = (c['delta_X'] + c['kE_pE']) * c['x'] + c['f']
    th = c['theta']
    # f_e such that a share `fail` of entrants never operates: a* = (1-fail)^(-1/theta), Pareto scale 1
    a_star = (1 - c['fail']) ** (-1.0 / th)
    fe = Phi / ((th - 1) * (c['r'] + c['deltaP']) * a_star ** th)
    K0 = yK ** (-1.0 / (1 - al))           # N0 = 1 at z0 = 1 with L0 = 1
    p = em.P(alpha=al, omega=omega, sigma=sigma, K=K0, L=1.0, yK=yK, r=c['r'], deltaP=c['deltaP'],
             fe=fe, Phi=Phi, tau=c['tau'], u=c['u'], x=c['x'], theta=th, A=1.0)
    p0 = float(em.P_LR(1.0, p))             # initial marginal product of machine services at z0 = 1
    p['A'] = em.breakeven_price(p, 1.0) / p0
    p['_cal'] = c
    p['_psiM0'] = psiM0
    p['_sE'] = c['kE_pE'] * c['x'] / Phi
    return p


def with_energy(p, kE_pE):
    """Same economy with a different energy cost per unit of compute (changes Phi)."""
    q = dict(p)
    c = q['_cal']
    q['Phi'] = (c['delta_X'] + kE_pE) * c['x'] + c['f']
    return q