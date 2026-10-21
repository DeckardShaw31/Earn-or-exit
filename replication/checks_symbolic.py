"""Symbolic verification (sympy) of core derivations in 'Earn or Terminate?' (revision).
Run with exec(); results collected in dict `res` (a residual of 0 means the identity holds)."""
import sympy as sp
res = {}
al, om, sg, K, L, M, z, yK = sp.symbols('alpha omega sigma K L M z y_K', positive=True)
nu = (sg - 1) / sg
N = (om * L**nu + (1 - om) * M**nu)**(1 / nu)
Y = K**al * N**(1 - al)
pM = sp.diff(Y, M)
psiM = (1 - om) * M**nu / (om * L**nu + (1 - om) * M**nu)
psiL = 1 - psiM
# S1: short-run price flexibility  -dln pM/dln M = psi_L/sigma + alpha psi_M
res['S1_shortrun_elasticity_residual'] = sp.simplify(sp.simplify(sp.diff(sp.log(pM), M) * M + (psiL / sg + al * psiM)))
# S2: long-run flexibility with K = yK^(-1/(1-alpha)) N  ->  psi_L/sigma
Klr = yK**(-1 / (1 - al)) * N
pLR = sp.diff(Y, M).subs(K, Klr)
res['S2_longrun_elasticity_residual'] = sp.simplify(sp.simplify(sp.diff(sp.log(pLR), M) * M + psiL / sg))
# S8: eta_S > 1 <=> psi_M < (1-sigma)/(1-alpha sigma)
pm = sp.symbols('psi_M', positive=True)
etaS = (1 - pm) / sg + al * pm
res['S8_threshold_psiM'] = [sp.simplify(s) for s in sp.solve(sp.Eq(etaS, 1), pm)]
res['S8_d_etaS_d_psiM'] = sp.simplify(sp.diff(etaS, pm))
# S4/S5: free entry with Pareto capability
a, astar, am, th, Phi, F = sp.symbols('a a_star a_m theta Phi F', positive=True)
g = th * am**th * a**(-th - 1)
j = sp.simplify(sp.integrate((a / astar - 1) * g, (a, astar, sp.oo), conds='none'))
res['S5_j_pareto'] = j
ast = sp.solve(sp.Eq(Phi * j, F), astar)[0]
res['S5_astar'] = ast
res['S5_elast_astar_Phi'] = sp.simplify(sp.diff(sp.log(ast), Phi) * Phi)
res['S5_elast_pstar_Phi'] = sp.simplify(sp.diff(sp.log(Phi / ast), Phi) * Phi)
res['S5_elast_astar_F'] = sp.simplify(sp.diff(sp.log(ast), F) * F)
tail = sp.integrate(a * g, (a, astar, sp.oo), conds='none')
res['S4_jprime_residual'] = sp.simplify(sp.diff(j, astar) + tail / astar**2)
# S6: machine wealth share with revenue tax and transfers
tau, sH, sW, G, thw = sp.symbols('tau s_H s_W Gamma Theta', positive=True)
gAI = (1 - tau) * G
gH = sH * G + sW * tau * G * thw / (1 - thw)
thdot = sp.simplify(thw * (1 - thw) * (gAI - gH))
res['S6_theta_star'] = [sp.simplify(t) for t in sp.solve(sp.Eq(thdot / thw, 0), thw)]
ts = (1 - tau - sH) / (1 - tau - sH + sW * tau)
res['S6_factorised_residual'] = sp.simplify(thdot - G * (1 - tau - sH + sW * tau) * thw * (ts - thw))
res['S6_jacobian_at_star'] = sp.simplify(sp.diff(thdot, thw).subs(thw, ts))
res['S6_dthetastar_dtau'] = sp.factor(sp.simplify(sp.diff(ts, tau)))
res['S6_tau_for_half'] = sp.solve(sp.Eq(ts, sp.Rational(1, 2)), tau)
res['S6_draft_tau_coexist_gives_theta'] = sp.simplify(ts.subs(tau, (1 - sH) / (1 - sH + sW)))
# S7: escape integrals int_1^inf (1 + a^q)/a^beta da
for (qq, bb) in [(0.5, 2), (1, 2), (1.5, 2), (0, 1)]:
    res[f'S7_integral_q{qq}_beta{bb}'] = sp.integrate((1 + a**sp.nsimplify(qq)) / a**sp.nsimplify(bb), (a, 1, sp.oo))

if __name__ == "__main__":
    for name, value in res.items():
        print(f"{name} => {value}")