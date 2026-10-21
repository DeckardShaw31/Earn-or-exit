"""Numerical verification of the propositions in 'Earn or Terminate?' (revision).
Each check appends (name, passed, detail) to `results`.  Run from the project root with exec()."""
import sys, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, 'code')
import eot_model as em
from scipy.optimize import brentq
from scipy.integrate import solve_ivp, quad
from scipy.special import ndtr, gammaincc
rng = np.random.default_rng(20261015)
results = []


def rec(name, ok, detail=''):
    results.append((name, bool(ok), detail))


def rand_params():
    return em.P(alpha=rng.uniform(0.2, 0.45), omega=rng.uniform(0.3, 0.9),
                sigma=float(rng.choice([rng.uniform(0.2, 0.95), rng.uniform(1.05, 4.0), 1.0])),
                K=rng.uniform(0.5, 5), L=rng.uniform(0.5, 2), yK=rng.uniform(0.15, 0.6),
                r=rng.uniform(0.02, 0.08), deltaP=rng.uniform(0.1, 0.6), fe=rng.uniform(0.2, 3),
                Phi=rng.uniform(0.2, 3), tau=rng.uniform(0, 0.4), u=rng.uniform(0, 0.4),
                x=rng.uniform(0.5, 2), theta=rng.uniform(1.5, 6), A=rng.uniform(0.3, 3))


# N1: closed-form long-run price equals the marginal product with K = yK^{-1/(1-alpha)} N
bad = 0
for _ in range(300):
    p = rand_params(); z = np.exp(rng.uniform(-5, 5)); L = p['L']; M = z * L
    if em.is_cd(p):
        N = L ** p['omega'] * M ** (1 - p['omega'])
    else:
        nu = em.nu_of(p); N = (p['omega'] * L ** nu + (1 - p['omega']) * M ** nu) ** (1 / nu)
    q = dict(p); q['K'] = p['yK'] ** (-1 / (1 - p['alpha'])) * N
    bad += abs(em.log_pM(M, q) - em.log_P_LR(z, p)) > 1e-9
rec('N1 long-run price closed form', bad == 0, f'{bad} mismatches / 300')

# N2: P(z) strictly decreasing; p_c is the supremum (sigma<1) or infimum (sigma>1)
bad = 0
for _ in range(300):
    p = rand_params()
    span = 25.0 / max(abs(em.nu_of(p)), 1e-9) if not em.is_cd(p) else 18.0
    zz = np.exp(np.linspace(-span, span, 2001)); lP = em.log_P_LR(zz, p)
    if np.any(np.diff(lP) >= 0): bad += 1; continue
    pc = em.p_crit(p)
    if pc is None: continue
    nu = abs(em.nu_of(p)); far = np.exp(min(60.0 / nu, 700.0))
    if p['sigma'] < 1:
        bad += not (np.all(np.exp(lP) < pc) and abs(em.P_LR(1 / far, p) / pc - 1) < 1e-9)
    else:
        bad += not (np.all(np.exp(lP) > pc) and abs(em.P_LR(far, p) / pc - 1) < 1e-9)
rec('N2 long-run price monotone, bounded by p_c', bad == 0, f'{bad} failures / 300')

# N3: short-run cutoff equilibrium (continuum, atomless F with finite mean)
bad = 0
def make_F(kind):
    if kind == 0:
        s_ = rng.uniform(0.2, 1.5)
        return (lambda c: np.exp(s_ ** 2 / 2) * ndtr((s_ ** 2 - np.log(c)) / s_), np.exp(-4 * s_), np.exp(4 * s_))
    if kind == 1:
        k_ = rng.uniform(0.5, 4)
        return (lambda c: k_ * gammaincc(k_ + 1, c), 1e-6, k_ + 12 * np.sqrt(k_) + 20)
    if kind == 2:
        lo_, w_ = 0.1, rng.uniform(0.5, 3)
        return (lambda c: ((lo_ + w_) ** 2 - np.clip(c, lo_, lo_ + w_) ** 2) / (2 * w_), lo_, lo_ + w_ * (1 - 1e-9))
    b_ = rng.uniform(1.5, 5)
    return (lambda c: b_ * np.maximum(c, 1.0) ** (1 - b_) / (b_ - 1), 1.0, 1e6)
for it in range(400):
    p = rand_params(); tailmean, c_lo, c_hi = make_F(it % 4); n0 = rng.uniform(0.2, 5)
    kk = (1 - p['tau']) * (1 - p['u']) * p['x']
    Mbar = lambda c: n0 * (1 - p['u']) * p['x'] * tailmean(c)
    hfun = lambda c: c - p['Phi'] / (kk * em.pM(Mbar(c), p))
    grid = np.exp(np.linspace(np.log(c_lo), np.log(c_hi), 800))
    h = np.array([hfun(c) for c in grid])
    sc = int(np.sum(np.diff(np.sign(h)) != 0))
    ok = np.all(np.diff(h) > 0) and sc <= 1 and (sc == 1 or h[0] >= 0)
    if sc == 1:
        k = int(np.argmax(h >= 0)); c = brentq(hfun, grid[k - 1], grid[k])
        ok = ok and abs(kk * c * em.pM(Mbar(c), p) - p['Phi']) < 1e-8 * p['Phi']
    bad += not ok
rec('N3 short-run cutoff equilibrium exists and is unique (continuum)', bad == 0, f'{bad} failures / 400')

# N4: d ln(A p_M(A Lambda))/d ln A = 1 - eta_SR ; eta_SR>1 iff sigma<1 and psi_M < (1-sigma)/(1-alpha sigma)
bad = 0
for _ in range(300):
    p = rand_params(); Lam = np.exp(rng.uniform(-4, 4)); h = 1e-6
    f = lambda lA: lA + em.log_pM(np.exp(lA) * Lam, p)
    d = (f(h) - f(-h)) / (2 * h)
    eta = em.eta_SR(Lam, p); psm = em.psiM_fixed(Lam, p)
    pred = (p['sigma'] < 1) and (psm < (1 - p['sigma']) / (1 - p['alpha'] * p['sigma']))
    bad += (abs(d - (1 - eta)) > 1e-6) or ((eta > 1) != pred)
rec('N4 local capability-revenue condition', bad == 0, f'{bad} failures / 300')

# N5: free entry holds at the break-even price; cutoff independent of K, sigma, tau
bad = 0
for _ in range(300):
    p = rand_params(); ps = em.breakeven_price(p)
    v = em.value_of_entry_const_price(ps, p)
    q = dict(p); q.update(K=p['K'] * 3, sigma=2.5 if p['sigma'] < 1 else 0.5, tau=0.0)
    bad += (abs(v / p['fe'] - 1) > 1e-9) or (abs(em.free_entry_cutoff(q) - em.free_entry_cutoff(p)) > 1e-14)
rec('N5 free-entry block recursion', bad == 0, f'{bad} failures / 300')

# N6: long-run compute elasticity d ln X*/d ln A = sigma/psi_L - 1
bad = 0; nfin = 0
for _ in range(400):
    p = rand_params(); s = em.stationary_LR(p)
    if s['regime'] != 'finite': continue
    h = 1e-5
    s_up = em.stationary_LR(p, A=p['A'] * np.exp(h)); s_dn = em.stationary_LR(p, A=p['A'] * np.exp(-h))
    if s_up['regime'] != 'finite' or s_dn['regime'] != 'finite': continue
    nfin += 1
    el = (np.log(s_up['X']) - np.log(s_dn['X'])) / (2 * h)
    bad += abs(el - (p['sigma'] / s['psiL'] - 1)) > 1e-4 * max(1, abs(el))
rec('N6 compute elasticity sigma/psi_L - 1', bad == 0, f'{bad} failures / {nfin} finite cases')

# N7: long-run regime classification and the value of entry at every z
bad = 0
for _ in range(400):
    p = rand_params(); s = em.stationary_LR(p); pc = em.p_crit(p)
    if pc is None: bad += s['regime'] != 'finite'; continue
    if p['sigma'] < 1: bad += (s['regime'] == 'nonviable') != (s['price'] >= pc)
    else: bad += (s['regime'] == 'unbounded') != (s['price'] <= pc)
    zz = np.logspace(-20, 20, 81)
    ve = np.array([em.value_of_entry_const_price(em.P_LR(zv, p), p) for zv in zz])
    if s['regime'] == 'unbounded': bad += not np.all(ve > p['fe'])
    if s['regime'] == 'nonviable': bad += not np.all(ve < p['fe'])
rec('N7 long-run regime classification', bad == 0, f'{bad} failures / 400')

# N8: hump-shaped compute under sigma<1 with peak where psi_L = sigma; monotone for sigma >= 1
bad = 0
for sg in [0.3, 0.5, 0.7, 0.9]:
    p = em.P(sigma=sg, omega=0.5)
    Ah = em.critical_capability(p)
    As = Ah * np.exp(np.linspace(1e-3, 12 / (1 - sg), 6000)); X = []; psl = []
    for A in As:
        s = em.stationary_LR(p, A=A); X.append(s['X']); psl.append(s['psiL'])
    X = np.array(X); psl = np.array(psl); i = int(np.argmax(X))
    bad += not (0 < i < len(X) - 1 and abs(psl[i] - sg) < 5e-3)
for sg in [1.0, 1.5, 3.0]:
    p = em.P(sigma=sg, omega=0.5)
    Ah = em.critical_capability(p); Amax = Ah * 0.999 if Ah else 1e3
    As = np.exp(np.linspace(np.log(Amax) - 8, np.log(Amax), 2000))
    X = np.array([em.stationary_LR(p, A=A)['X'] for A in As])
    bad += not np.all(np.diff(X) > 0)
rec('N8 hump (sigma<1, peak at psi_L=sigma) / monotone (sigma>=1)', bad == 0, f'{bad} failures / 7')

# N9: capability shock: overhang (shakeout) iff long-run compute falls iff spending falls
bad = 0; nover = 0
for _ in range(300):
    p0 = rand_params(); D = rng.uniform(0.05, 1.5); p1 = dict(p0); p1['A'] = p0['A'] * np.exp(D)
    tr = em.transition(p0, p1); s0, s1 = tr['s0'], tr['s1']
    over = tr['case'] == 'overhang'; nover += over
    M0 = s0['M']; spend_falls = em.pM(np.exp(D) * M0, p0) * np.exp(D) * M0 < em.pM(M0, p0) * M0
    bad += (over != (s1['n'] < s0['n'])) or (over != spend_falls)
    if over: bad += not (tr['a_s'] > s0['a_tilde'] and tr['M0plus'] > s1['M'] and tr['T'] > 0)
rec('N9 capability shock: shakeout <=> compute falls <=> spending falls', bad == 0, f'{bad} failures / 300 ({nover} overhang)')

# N10a: operating-cost shock (Pareto, interior cutoffs): overhang iff spending falls as M contracts by kappa
bad = 0; nover = 0; ncase = 0
for _ in range(300):
    p0 = rand_params(); p1 = dict(p0); p1['Phi'] = p0['Phi'] * np.exp(rng.uniform(0.05, 1.0))
    a0 = em.free_entry_cutoff(p0); a1 = em.free_entry_cutoff(p1)
    if a0 < 1 or a1 < 1: continue
    ncase += 1
    tr = em.transition(p0, p1); over = tr['case'] == 'overhang'; nover += over
    ks = (a1 / a0) ** (p0['theta'] - 1)
    M0 = tr['s0']['M']
    spend_falls = em.pM(M0 / ks, p0) * (M0 / ks) < em.pM(M0, p0) * M0 * (1 + 1e-12)
    bad += over != spend_falls
rec('N10a cost shock: overhang <=> elastic demand (Pareto)', bad == 0, f'{bad} failures / {ncase} ({nover} overhang)')

# N10b: tax increase: always overhang, long-run cutoff unchanged, exit at t=0 if the cutoff is interior
bad = 0
for _ in range(200):
    p0 = rand_params(); p1 = dict(p0); p1['tau'] = min(0.95, p0['tau'] + rng.uniform(0.02, 0.5))
    tr = em.transition(p0, p1)
    interior = tr['s0']['a_tilde'] > 1.0
    bad += not (tr['case'] == 'overhang' and abs(tr['s1']['a_tilde'] - tr['s0']['a_tilde']) < 1e-14
                and ((tr['exit_share'] > 0) or not interior))
rec('N10b tax shock: overhang, LR cutoff unchanged, exit if cutoff interior', bad == 0, f'{bad} failures / 200')

# N11: entry unprofitable during the overhang (zero buffer and deep pocket); value -> f_e at T
bad = 0; cnt = 0
for _ in range(60):
    p0 = em.P(sigma=rng.uniform(0.2, 0.6), omega=rng.uniform(0.4, 0.8), theta=rng.uniform(2, 5),
              deltaP=rng.uniform(0.15, 0.5)); p1 = dict(p0); p1['A'] = np.exp(rng.uniform(0.2, 1.0))
    tr = em.transition(p0, p1)
    if tr['case'] != 'overhang': continue
    cnt += 1
    for te in np.linspace(0, tr['T'] * 0.999, 7):
        bad += em.value_of_entry_path(tr, p1, te) >= p1['fe']
        bad += em.value_of_entry_path(tr, p1, te, deep_pocket=True) >= p1['fe']
    bad += abs(em.value_of_entry_path(tr, p1, tr['T'] * 1.0001) / p1['fe'] - 1) > 1e-6
rec('N11 entry unprofitable during overhang (both buffer regimes)', bad == 0, f'{bad} failures in {cnt} paths')

# N12: deep pockets: max(a0*, a1*) < a_d < a_s and T_d > T for capability, cost and tax shocks, on overhang paths
#      whose zero-buffer exit wave is NONEMPTY (a_s above the lowest incumbent capability, max(1, a0*) under
#      Pareto scale 1).  The complementary, degenerate case (empty exit wave: no exit in either regime, identical
#      paths, T_d = T) is verified separately in N12b, so no draw is discarded unchecked.
bad = 0; cnt = 0; n12_degenerate = []
for it in range(600):
    p0 = em.P(sigma=rng.uniform(0.2, 2.0), omega=rng.uniform(0.4, 0.8), theta=rng.uniform(2, 5),
              deltaP=rng.uniform(0.15, 0.5), r=rng.uniform(0.02, 0.08), fe=rng.uniform(0.2, 0.8))
    p1 = dict(p0)
    if it % 3 == 0: p1['A'] = np.exp(rng.uniform(0.2, 1.0))
    elif it % 3 == 1: p1['Phi'] = p0['Phi'] * np.exp(rng.uniform(0.05, 0.8))
    else: p1['tau'] = p0['tau'] + rng.uniform(0.05, 0.4)
    tr = em.transition(p0, p1)
    if tr['case'] != 'overhang': continue
    if tr['a_s'] <= max(1.0, tr['s0']['a_tilde']):                  # empty zero-buffer exit wave -> N12b
        n12_degenerate.append((p0, p1, tr)); continue
    cnt += 1
    dp = em.deep_pocket_path(p0, p1)
    lo = max(tr['s0']['a_tilde'], tr['s1']['a_tilde'])
    bad += not (lo < dp['a_d'] < tr['a_s'] and dp['T'] > tr['T'])
rec('N12 deep-pocket cutoff strictly inside (a*, a_s); longer overhang (nonempty exit wave)', bad == 0, f'{bad} failures in {cnt} paths')

# N13: machine wealth share with time-varying Gamma_t.  In Gamma-time s = int_0^t Gamma, the law of motion is the logistic
# (Bernoulli) equation dTheta/ds = k Theta - b Theta^2, k = 1 - tau - s_H, b = k + s_W tau, with closed form 1/Theta(s) =
# b/k + (1/Theta_0 - b/k) e^{-k s}.  Checks: (i) the numerical ODE solution matches the closed form at the final date;
# (ii) the closed form's limit (s -> inf, since Gamma is bounded below) equals Theta*(tau) if k > 0 and 0 if k <= 0;
# (iii) the closed form at s = 1e7 is within 1e-6 of that limit (|k| >= 1e-5).  Replaces a fixed-horizon test whose
# tolerance was violated only by slow convergence (rate Gamma |k|) near tau = 1 - s_H.
bad = 0; worst = 0.0
for _ in range(200):
    tau = rng.uniform(0.01, 0.9); sH = rng.uniform(0.05, 0.6); sW = rng.uniform(0.01, 0.4); th0 = rng.uniform(0.01, 0.99)
    G = lambda t: 0.1 + 0.08 * np.sin(0.3 * t) ** 2
    rhs = lambda t, th: G(t) * th * ((1 - tau - sH) * (1 - th) - sW * tau * th)
    Tend = 300.0
    sol = solve_ivp(rhs, [0, Tend], [th0], rtol=1e-11, atol=1e-14, method='DOP853')
    S = 0.1 * Tend + 0.08 * (Tend / 2 - np.sin(0.6 * Tend) / 1.2)          # int_0^T Gamma(t) dt
    k = 1 - tau - sH; b = k + sW * tau
    inv = lambda s: (b / k + (1 / th0 - b / k) * np.exp(-k * s)) if abs(k) > 1e-14 else 1 / th0 + b * s
    err = abs(sol.y[0, -1] - 1 / inv(S)); worst = max(worst, err)
    lim = k / b if k > 0 else 0.0
    target = (1 - tau - sH) / (1 - tau - sH + sW * tau) if tau < 1 - sH else 0.0
    far = 1 / inv(1e7) if abs(k) >= 1e-5 else lim
    bad += not (err < 1e-8 and abs(lim - target) < 1e-14 and abs(far - lim) < 1e-6)
rec('N13 machine wealth share: ODE = closed form; limit Theta*(tau) or 0', bad == 0, f'{bad} failures / 200; max |ODE - closed form| = {worst:.1e}')

# N14: escape integrability: finite-time escape iff q < beta - 1 (exponent of the growth law minus one)
bad = 0
for (qq, bb) in [(0.2, 1.5), (0.6, 1.5), (0.5, 2.0), (1.0, 2.0), (0.0, 1.0), (0.3, 1.0)]:
    tails = [quad(lambda a: (1 + 0.5 * a ** qq) / a ** bb, 10 ** k, 10 ** (k + 1))[0] for k in range(2, 7)]
    bad += (tails[-1] < 0.5 * tails[0]) != (qq < bb - 1)
rec('N14 escape integrability condition', bad == 0, f'{bad} failures / 6')

# N15: general cost pass-through (lognormal capability): dln p*/dln Phi = a*/E[a|a>=a*]
s_ = 0.7
tm = lambda c: np.exp(s_ ** 2 / 2) * ndtr((s_ ** 2 - np.log(c)) / s_)
tms = lambda c: ndtr((-np.log(c)) / s_)
jj = lambda c: tm(c) / c - tms(c)
cut = lambda Phi, F: brentq(lambda c: Phi * jj(c) - F, 1e-8, 1e8)
Phi0, F0, h = 1.3, 0.4, 1e-6
c0 = cut(Phi0, F0); rho = c0 * tms(c0) / tm(c0)
el = (np.log(Phi0 * np.exp(h) / cut(Phi0 * np.exp(h), F0)) - np.log(Phi0 * np.exp(-h) / cut(Phi0 * np.exp(-h), F0))) / (2 * h)
rec('N15 cost pass-through equals marginal-to-average capability ratio', abs(el - rho) < 1e-6, f'elasticity {el:.8f} vs ratio {rho:.8f}')


# N12b: degenerate overhang (empty zero-buffer exit wave): no exit at t = 0 in either regime and identical paths, T_d = T.
# Besides the degenerate draws met in N12, 150 targeted draws with a high entry cost, f_e > Phi/((theta-1)(r+deltaP)),
# put the pre-shock cutoff below the support (no failed entry), where small shocks leave every incumbent solvent at t = 0.
for it in range(150):
    th_, dP_, r_ = rng.uniform(2, 5), rng.uniform(0.15, 0.5), rng.uniform(0.02, 0.08)
    p0 = em.P(sigma=rng.uniform(0.2, 2.0), omega=rng.uniform(0.4, 0.8), theta=th_, deltaP=dP_, r=r_)
    p0['fe'] = p0['Phi'] / ((th_ - 1) * (r_ + dP_)) * rng.uniform(1.05, 3.0)
    p1 = dict(p0)
    if it % 3 == 0: p1['A'] = np.exp(rng.uniform(0.02, 0.3))
    elif it % 3 == 1: p1['Phi'] = p0['Phi'] * np.exp(rng.uniform(0.01, 0.15))
    else: p1['tau'] = p0['tau'] + rng.uniform(0.01, 0.1)
    tr = em.transition(p0, p1)
    if tr['case'] == 'overhang' and tr['a_s'] <= max(1.0, tr['s0']['a_tilde']):
        n12_degenerate.append((p0, p1, tr))
bad = 0
for (p0, p1, tr) in n12_degenerate:
    dp = em.deep_pocket_path(p0, p1)
    bad += not (abs(tr['exit_share']) < 1e-12 and abs(dp['exit_share']) < 1e-12 and abs(dp['T'] - tr['T']) < 1e-10
                and np.allclose(dp['M'], tr['M'], rtol=1e-10))
rec('N12b empty exit wave: no exit in either regime, identical overhang (T_d = T)', bad == 0,
    f'{bad} failures in {len(n12_degenerate)} paths')

# N16: frontier growth.  Entrants at t draw a = A0 e^{gt} a~, a~ ~ Pareto(theta, 1); on a balanced path the price falls at
# rate g.  Checks: (a) closed-form inner value = quadrature; (b) entry value decreasing in the normalized cutoff and in g,
# so the cutoff a0(g) is unique and decreasing in g; (c) a0(g) -> stationary cutoff as g -> 0; (d) simulated cash flow of a
# provider turns negative exactly at age ln(a~/a0)/g; (e) sigma = 1, K fixed: entry growing at g(1/eta_S - 1) makes M grow
# at g/eta_S and the price fall at exactly g (cohort integral evaluated at two dates).
def inner_cf(R, g, rho):                      # int_0^{ln R / g} e^{-rho s} (R e^{-g s} - 1) ds, R >= 1
    return (R - R ** (-rho / g)) / (rho + g) - (1 - R ** (-rho / g)) / rho
def V_front(a0, g, th, rho):
    f = lambda at: inner_cf(at / a0, g, rho) * th * at ** (-th - 1)
    return quad(f, max(a0, 1.0), np.inf, limit=400)[0]
bad_a = bad_b = bad_c = bad_d = bad_e = 0
for _ in range(40):
    th = rng.uniform(1.8, 5); rho = rng.uniform(0.15, 1.0); Phi = rng.uniform(0.3, 3); fe = rng.uniform(0.05, 1.0)
    # (a)
    R = np.exp(rng.uniform(0.01, 3)); g = rng.uniform(0.05, 2)
    num_ = quad(lambda s: np.exp(-rho * s) * (R * np.exp(-g * s) - 1), 0, np.log(R) / g)[0]
    bad_a += abs(num_ - inner_cf(R, g, rho)) > 1e-9 * max(1, abs(num_))
    # (b)
    gs = [0.05, 0.25, 0.5, 1.0, 2.0]
    a0s = [brentq(lambda la: Phi * V_front(np.exp(la), gg, th, rho) - fe, -20, 20, xtol=1e-12) for gg in gs]
    bad_b += not all(np.diff(a0s) < 0)
    a_ = np.exp(rng.uniform(-1, 1))
    bad_b += not (V_front(a_ * 1.01, 0.5, th, rho) < V_front(a_, 0.5, th, rho) and
                  V_front(a_, 0.6, th, rho) < V_front(a_, 0.5, th, rho))
    # (c) small-g limit versus the stationary Pareto cutoff solving Phi j(a) = rho fe
    a_st = brentq(lambda la: Phi * float(em.j_fun(np.exp(la), em.P(theta=th, A=1.0))) - rho * fe, -20, 20, xtol=1e-12) \
        if hasattr(em, 'j_fun') else None
    a_g0 = np.exp(brentq(lambda la: Phi * V_front(np.exp(la), 1e-5, th, rho) - fe, -20, 20, xtol=1e-12))
    a_st = np.exp(a_st) if a_st is not None else None
    bad_c += (a_st is None) or abs(np.log(a_g0 / a_st)) > 1e-4
    # (d) exit age by simulation of the cash-flow path
    a0 = np.exp(a0s[2]); g = gs[2]; at = a0 * np.exp(rng.uniform(0.05, 2.0))
    s_grid = np.linspace(0, 10, 200001); cf = at / a0 * np.exp(-g * s_grid) - 1
    s_cross = s_grid[np.argmax(cf < 0)]
    bad_d += abs(s_cross - np.log(at / a0) / g) > 1e-4
for _ in range(20):
    # (e) sigma = 1, K fixed: eta_S = omega + alpha (1 - omega)
    al = rng.uniform(0.2, 0.45); om = rng.uniform(0.3, 0.9); th = rng.uniform(1.8, 5); dP = rng.uniform(0.1, 0.8)
    g = rng.uniform(0.05, 1.5); a0 = np.exp(rng.uniform(-0.5, 1.0)); etaS = om + al * (1 - om); gam = g * (1 / etaS - 1)
    Tm = lambda a: th / (th - 1) * max(a, 1.0) ** (1 - th)                 # int_a^inf s dG(s), Pareto scale 1
    def M_at(t):                                                          # cohort integral with J(v) = e^{gam v}
        f = lambda s: np.exp(gam * (t - s)) * np.exp(-dP * s) * np.exp(g * (t - s)) * Tm(a0 * np.exp(g * s))
        b = max(0.0, -np.log(a0) / g)                                      # kink where a0 e^{gs} crosses 1
        v = (quad(f, 0, b, limit=400)[0] if b > 0 else 0.0) + quad(f, b, np.inf, limit=400)[0]
        assert np.isfinite(v) and v > 0
        return v
    gM = np.log(M_at(1.0) / M_at(0.0))
    gp = -etaS * gM                                                       # Cobb-Douglas: d ln p_M = -eta_S d ln M
    bad_e += abs(gM - g / etaS) > 1e-7 or abs(gp + g) > 1e-7
rec('N16 frontier growth: closed form, unique cutoff decreasing in g, g->0 limit, exit age ln(a/a0)/g, BGP supply',
    bad_a + bad_b + bad_c + bad_d + bad_e == 0, f'{bad_a + bad_b + bad_c + bad_d + bad_e} failures across subchecks a-e (40 + 20 draws)')

# N17: closed form of Corollary (critical capability): psi_M* = (A / A_hat)^(sigma - 1) whenever the LR state is finite
bad = 0; cnt = 0
for _ in range(400):
    p = rand_params()
    if p['sigma'] == 1.0: continue
    s = em.stationary_LR(p)
    if s['regime'] != 'finite': continue
    cnt += 1
    Ah = em.critical_capability(p)
    bad += abs((1 - s['psiL']) - (p['A'] / Ah) ** (p['sigma'] - 1)) > 1e-8
rec('N17 closed form psi_M* = (A/A_hat)^(sigma-1)', bad == 0 and cnt > 0, f'{bad} failures / {cnt} finite cases')

for r_ in results:
    print(('PASS ' if r_[1] else 'FAIL ') + r_[0] + '  [' + r_[2] + ']')