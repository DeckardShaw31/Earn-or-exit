"""
eot_model.py -- core objects for "Earn or Terminate?"

Production:  Y = K^alpha N^(1-alpha),  N = [omega L^nu + (1-omega) M^nu]^(1/nu),  nu = (sigma-1)/sigma.
Providers:   capability a = A * a_tilde, a_tilde ~ Pareto(scale 1, shape theta); fixed compute x;
             inference share (1-u); operating cost per provider Phi = c*x + f; revenue tax tau.
             Operating surplus pi(a) = (1-tau)(1-u) x a p_M - Phi.
Entry:       sunk cost f_e, exogenous termination hazard delta_P, sponsor discount rate r.
Short run:   K, L fixed.  Long run (general equilibrium): Y/K = y_K fixed by the capital closure.

All functions work for sigma = 1 (Cobb-Douglas limit).
"""
import numpy as np
from scipy.optimize import brentq
from scipy.special import expit
from scipy.integrate import quad

BASE = dict(alpha=0.33, omega=0.65, sigma=0.6, K=1.0, L=1.0, yK=0.30,
            r=0.04, deltaP=0.33, fe=1.0, Phi=1.0, tau=0.0, u=0.0, x=1.0,
            theta=3.0, A=1.0)


def P(**kw):
    """Return a parameter dict: BASE updated with keyword overrides."""
    p = dict(BASE)
    p.update(kw)
    return p


def nu_of(p):
    return (p['sigma'] - 1.0) / p['sigma']


def is_cd(p):
    return abs(p['sigma'] - 1.0) < 1e-12


# ---------------------------------------------------------------- short-run (K, L fixed)
def log_pM(M, p):
    """log of p_M = dY/dM with K, L fixed."""
    al, om = p['alpha'], p['omega']
    lM, lL, lK = np.log(M), np.log(p['L']), np.log(p['K'])
    if is_cd(p):
        lN = om * lL + (1 - om) * lM
        return np.log((1 - al) * (1 - om)) + al * lK + (1 - al) * lN - lM
    nu = nu_of(p)
    lB = np.logaddexp(np.log(om) + nu * lL, np.log(1 - om) + nu * lM)
    lN = lB / nu
    return np.log((1 - al) * (1 - om)) + al * lK + (1 - al - nu) * lN + (nu - 1) * lM


def pM(M, p):
    return np.exp(log_pM(M, p))


def psiM_fixed(M, p):
    """Machine share of cognitive income, psi_M = s_M/(1-alpha)."""
    om = p['omega']
    if is_cd(p):
        return np.full_like(np.asarray(M, float), 1 - om)
    nu = nu_of(p)
    return expit(np.log(1 - om) + nu * np.log(M) - np.log(om) - nu * np.log(p['L']))


def eta_SR(M, p):
    """Short-run price flexibility -dln p_M/dln M = psi_L/sigma + alpha psi_M."""
    psm = psiM_fixed(M, p)
    return (1 - psm) / p['sigma'] + p['alpha'] * psm


def inv_pM(price, p, lo=-80.0, hi=80.0):
    """Machine services M solving p_M(M) = price (K, L fixed); exists for every price > 0."""
    f = lambda lm: log_pM(np.exp(lm), p) - np.log(price)
    return float(np.exp(brentq(f, lo, hi, xtol=1e-14, rtol=1e-13, maxiter=500)))


# ---------------------------------------------------------------- long-run (Y/K = yK)
def log_P_LR(z, p):
    al, om = p['alpha'], p['omega']
    c0 = np.log((1 - al) * (1 - om)) - (al / (1 - al)) * np.log(p['yK'])
    lz = np.log(z)
    if is_cd(p):
        return c0 - om * lz
    nu = nu_of(p)
    lB = np.logaddexp(np.log(om) - nu * lz, np.log(1 - om))
    return c0 + ((1 - nu) / nu) * lB


def P_LR(z, p):
    return np.exp(log_P_LR(z, p))


def psiL_LR(z, p):
    om = p['omega']
    if is_cd(p):
        return np.full_like(np.asarray(z, float), om)
    nu = nu_of(p)
    return expit(np.log(om) - nu * np.log(z) - np.log(1 - om))


def p_crit(p):
    """Critical price p_c = (1-alpha) yK^{-alpha/(1-alpha)} (1-omega)^{sigma/(sigma-1)}; None at sigma=1."""
    if is_cd(p):
        return None
    al, om, s = p['alpha'], p['omega'], p['sigma']
    return (1 - al) * p['yK'] ** (-al / (1 - al)) * (1 - om) ** (s / (s - 1))


# ---------------------------------------------------------------- Pareto capability (scale 1)
def tail_mass(at, p):
    """Pr(a_tilde >= at)."""
    at = np.asarray(at, float)
    return np.where(at <= 1.0, 1.0, np.maximum(at, 1.0) ** (-p['theta']))


def tail_mean(at, p):
    """E[a_tilde; a_tilde >= at] = int_at^inf s dG(s)."""
    th = p['theta']
    at = np.asarray(at, float)
    return np.where(at <= 1.0, th / (th - 1), th * np.maximum(at, 1.0) ** (1 - th) / (th - 1))


def j_fun(at, p):
    """j(a) = int_a^inf (s/a - 1) dG(s)."""
    return tail_mean(at, p) / at - tail_mass(at, p)


def free_entry_cutoff(p):
    """Normalized cutoff a_tilde* solving Phi j(a*) = (r + deltaP) f_e."""
    th = p['theta']
    R = (p['r'] + p['deltaP']) * p['fe'] / p['Phi']
    at = (1.0 / ((th - 1) * R)) ** (1.0 / th)
    if at >= 1.0:
        return at
    return th / ((th - 1) * (1.0 + R))


def breakeven_price(p, A=None):
    """Free-entry break-even price p* = Phi / ((1-tau)(1-u) x A a_tilde*)."""
    A = p['A'] if A is None else A
    return p['Phi'] / ((1 - p['tau']) * (1 - p['u']) * p['x'] * A * free_entry_cutoff(p))


def value_of_entry_const_price(price, p, A=None):
    """Value of entry at a constant price (zero buffer = deep pocket when prices are constant)."""
    A = p['A'] if A is None else A
    k = (1 - p['tau']) * (1 - p['u']) * p['x'] * A
    a0 = p['Phi'] / (k * price)
    return (k * price * tail_mean(a0, p) - p['Phi'] * tail_mass(a0, p)) / (p['r'] + p['deltaP'])


# ---------------------------------------------------------------- stationary equilibria
def stationary_fixedK(p, A=None):
    """Free-entry stationary equilibrium with K, L fixed (always exists)."""
    A = p['A'] if A is None else A
    at = free_entry_cutoff(p)
    ps = breakeven_price(p, A)
    M = inv_pM(ps, p)
    k = (1 - p['u']) * p['x'] * A
    J = p['deltaP'] * M / (k * float(tail_mean(at, p)))
    n = J * float(tail_mass(at, p)) / p['deltaP']
    return dict(a_tilde=at, price=ps, M=M, J=J, n=n, X=n * p['x'], eta=float(eta_SR(M, p)),
                psiM=float(psiM_fixed(M, p)))


def stationary_LR(p, A=None):
    """General-equilibrium stationary state with Y/K = yK.

    Returns dict with 'regime' in {'finite', 'nonviable', 'unbounded'} and, if finite, z*, n*, X*.
    """
    A = p['A'] if A is None else A
    at = free_entry_cutoff(p)
    ps = breakeven_price(p, A)
    pc = p_crit(p)
    if pc is not None:
        if p['sigma'] < 1 and ps >= pc:
            return dict(regime='nonviable', price=ps, pc=pc, a_tilde=at)
        if p['sigma'] > 1 and ps <= pc:
            return dict(regime='unbounded', price=ps, pc=pc, a_tilde=at)
    f = lambda lz: log_P_LR(np.exp(lz), p) - np.log(ps)
    z = float(np.exp(brentq(f, -200.0, 200.0, xtol=1e-14, rtol=1e-13, maxiter=1000)))
    k = (1 - p['u']) * p['x'] * A
    n = z * p['L'] * float(tail_mass(at, p)) / (k * float(tail_mean(at, p)))
    return dict(regime='finite', price=ps, pc=pc, a_tilde=at, z=z, n=float(n), X=float(n * p['x']),
                psiL=float(psiL_LR(z, p)))


def critical_capability(p):
    """A_hat = p~*/p_c, where p~* is the break-even price at A = 1."""
    pc = p_crit(p)
    return None if pc is None else breakeven_price(p, 1.0) / pc


# ---------------------------------------------------------------- transitions (K, L fixed)
def transition(p0, p1, horizon=40.0, npts=4001):
    """Equilibrium path after a permanent, unanticipated shock from parameters p0 to p1 at t = 0.

    Incumbents: stationary population of p0 (density (J0/deltaP) g(a_tilde) on [a0*, inf)); the capability
    scale switches to p1['A'].  Zero buffers: providers exit when current cash flow < 0.
    Returns dict with the time path and the case ('overhang' or 'immediate').
    """
    s0 = stationary_fixedK(p0)
    s1 = stationary_fixedK(p1)
    d = p1['deltaP']
    A1 = p1['A']
    k1 = (1 - p1['u']) * p1['x'] * A1
    kk = (1 - p1['tau']) * k1
    J0, a0 = s0['J'], s0['a_tilde']
    Minc = lambda at: k1 * (J0 / p0['deltaP']) * float(tail_mean(max(at, a0), p1))
    nInc = lambda at: (J0 / p0['deltaP']) * float(tail_mass(max(at, a0), p1))
    a1 = s1['a_tilde']
    Mbar = Minc(max(a1, a0))
    t = np.linspace(0.0, horizon, npts)
    out = dict(t=t, s0=s0, s1=s1)
    if Mbar <= s1['M'] * (1 + 1e-12):
        out['case'] = 'immediate'
        a_exit = max(a1, a0)
        entry_mass = (s1['M'] - Mbar) / (k1 * float(tail_mean(a1, p1)))
        n_inc0 = nInc(a_exit)
        n_ent0 = entry_mass * float(tail_mass(a1, p1))
        n = (n_inc0 + n_ent0) * np.exp(-d * t) + s1['n'] * (1 - np.exp(-d * t))
        out.update(a_s=a_exit, entry_mass0=entry_mass, T=0.0, M=np.full_like(t, s1['M']),
                   price=np.full_like(t, s1['price']), n=n, exit_share=1 - n_inc0 / s0['n'],
                   M0plus=s1['M'])
        return out
    g = lambda la: la + np.log(kk) + log_pM(Minc(np.exp(la)), p1) - np.log(p1['Phi'])
    lo = np.log(max(a1, a0))
    hi = lo + 1.0
    while g(hi) < 0:
        hi += 1.0
    a_s = float(np.exp(brentq(g, lo, hi, xtol=1e-14, rtol=1e-13)))
    M0p = Minc(a_s)
    T = np.log(M0p / s1['M']) / d
    Mt = np.where(t < T, M0p * np.exp(-d * t), s1['M'])
    n_s = nInc(a_s)
    nT = n_s * np.exp(-d * T)
    n = np.where(t < T, n_s * np.exp(-d * t),
                 nT * np.exp(-d * (t - T)) + s1['n'] * (1 - np.exp(-d * (t - T))))
    out.update(case='overhang', a_s=a_s, T=T, M=Mt, price=pM(Mt, p1), n=n, M0plus=M0p,
               exit_share=1 - n_s / s0['n'])
    return out


def path_price_fun(tr, p1):
    """Callable price(t) for an overhang path (closed form between 0 and T)."""
    s1 = tr['s1']
    d = p1['deltaP']
    M0p, T = tr['M0plus'], tr['T']

    def price(tt):
        if tt >= T:
            return s1['price']
        return float(pM(M0p * np.exp(-d * tt), p1))
    return price


def value_of_entry_path(tr, p1, t_entry, deep_pocket=False):
    """Value of entering at t_entry along an (overhang) price path."""
    s1 = tr['s1']
    price = path_price_fun(tr, p1)
    rd = p1['r'] + p1['deltaP']
    T = tr['T']
    kk = (1 - p1['tau']) * (1 - p1['u']) * p1['x'] * p1['A']
    if t_entry < T:
        Ip = quad(lambda s: np.exp(-rd * (s - t_entry)) * price(s), t_entry, T, limit=200)[0]
        Ip += np.exp(-rd * (T - t_entry)) * s1['price'] / rd
    else:
        Ip = s1['price'] / rd
    if deep_pocket:
        a_op = p1['Phi'] / (rd * kk * Ip)
    else:
        a_op = p1['Phi'] / (kk * price(t_entry))
    return float(kk * Ip * tail_mean(a_op, p1) - p1['Phi'] / rd * tail_mass(a_op, p1))


def deep_pocket_cutoff(p0, p1):
    """Exit cutoff when incumbents can borrow freely (exit iff PV < 0), with the induced price path."""
    s0 = stationary_fixedK(p0)
    s1 = stationary_fixedK(p1)
    d, rd = p1['deltaP'], p1['r'] + p1['deltaP']
    k1 = (1 - p1['u']) * p1['x'] * p1['A']
    kk = (1 - p1['tau']) * k1
    J0, a0 = s0['J'], s0['a_tilde']
    Minc = lambda at: k1 * (J0 / p0['deltaP']) * float(tail_mean(max(at, a0), p1))

    def PV(ad):
        M0p = Minc(ad)
        if M0p <= s1['M']:
            return kk * ad * s1['price'] / rd - p1['Phi'] / rd
        T = np.log(M0p / s1['M']) / d
        I = quad(lambda s: np.exp(-rd * s) * pM(M0p * np.exp(-d * s), p1), 0, T, limit=200)[0]
        I += np.exp(-rd * T) * s1['price'] / rd
        return kk * ad * I - p1['Phi'] / rd

    lo = max(s1['a_tilde'], a0)
    if PV(lo) >= 0:
        return lo, PV
    hi = lo * 1.5
    while PV(hi) < 0:
        hi *= 1.5
    return brentq(PV, lo, hi, xtol=1e-13), PV


def deep_pocket_path(p0, p1, horizon=40.0, npts=4001):
    """Equilibrium path with deep-pocket incumbents (exit only at t = 0, below a_d)."""
    s0 = stationary_fixedK(p0)
    s1 = stationary_fixedK(p1)
    d = p1['deltaP']
    k1 = (1 - p1['u']) * p1['x'] * p1['A']
    J0, a0 = s0['J'], s0['a_tilde']
    ad, _ = deep_pocket_cutoff(p0, p1)
    M0p = k1 * (J0 / p0['deltaP']) * float(tail_mean(max(ad, a0), p1))
    n_d = (J0 / p0['deltaP']) * float(tail_mass(max(ad, a0), p1))
    t = np.linspace(0.0, horizon, npts)
    T = max(np.log(M0p / s1['M']) / d, 0.0)
    Mt = np.where(t < T, M0p * np.exp(-d * t), s1['M'])
    nT = n_d * np.exp(-d * T)
    n = np.where(t < T, n_d * np.exp(-d * t),
                 nT * np.exp(-d * (t - T)) + s1['n'] * (1 - np.exp(-d * (t - T))))
    return dict(t=t, a_d=ad, T=T, M=Mt, price=pM(Mt, p1), n=n, M0plus=M0p,
                exit_share=1 - n_d / s0['n'], s0=s0, s1=s1)