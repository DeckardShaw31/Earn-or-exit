"""
run_numerics.py -- tables, figures and cited numbers for the quantitative illustration.

Usage:  python local/artifacts/run_numerics.py
Outputs: table_shocks.{csv,tex}, table_sensitivity.{csv,tex}, table_calibration.tex,
         numbers.json and fig{1..4}_*.{pdf,png}, saved beside this script
"""
import os, sys, json
import numpy as np
import pandas as pd
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else 'code'
sys.path.insert(0, HERE)
import eot_model as em
import calibration as cb

def output_path(filename):
    return os.path.join(HERE, filename)

# ------------------------------------------------------------------ style (standalone fallback)
try:
    apply_figure_style(sizes=(8, 7, 6))                       # noqa: F821  (figure-style helper if loaded)
    _panel_letter = panel_letter                              # noqa: F821
except NameError:
    plt.rcParams.update({'font.size': 8, 'axes.titlesize': 8, 'axes.labelsize': 8, 'legend.fontsize': 7,
                         'xtick.labelsize': 6, 'ytick.labelsize': 6, 'xtick.direction': 'out',
                         'ytick.direction': 'out', 'legend.frameon': False, 'savefig.dpi': 300,
                         'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})

    def _panel_letter(ax, letter, dx=-0.18, dy=1.02, case='lower', fontsize=None):
        ax.text(dx, dy, letter, transform=ax.transAxes, fontweight='bold', fontsize=fontsize or 10,
                va='bottom', ha='left')

C_COMP, C_SUBS, C_NEAR, C_GREY = '#1f5aa6', '#c4581b', '#6a8fc2', '#8c8c8c'
num = {}


# ------------------------------------------------------------------ helpers
def shock_params(p0, kind, size=None):
    p1 = dict(p0)
    if kind == 'capability':
        p1['A'] = p0['A'] * float(np.exp(size if size is not None else p0['_cal']['Delta']))
    elif kind == 'energy':
        p1 = cb.with_energy(p0, p0['_cal']['kE_pE'] * size)
    elif kind == 'tax':
        p1['tau'] = size
    return p1


def respond(p0, p1):
    tr = em.transition(p0, p1)
    if tr['case'] == 'overhang':
        dp = em.deep_pocket_path(p0, p1)
        exit_dp, T_dp = dp['exit_share'], dp['T']
    else:
        dp, exit_dp, T_dp = None, tr['exit_share'], 0.0
    s0L, s1L = em.stationary_LR(p0), em.stationary_LR(p1)
    dX = np.log(s1L['X'] / s0L['X']) if s1L['regime'] == 'finite' else np.nan
    return tr, dp, dict(case=tr['case'], exit_zb=tr['exit_share'], exit_dp=exit_dp, T_zb=tr['T'], T_dp=T_dp,
                        dlnX_sr=np.log(tr['s1']['n'] / tr['s0']['n']),
                        dlnp=np.log(tr['s1']['price'] / tr['s0']['price']), dlnX_lr=dX, lr_regime=s1L['regime'])


# ------------------------------------------------------------------ Table 2: shock responses
SIGMAS = [0.6, 0.95, 2.0]
SHOCKS = [('Capability gain (x3)', 'capability', None), ('Energy price +50%', 'energy', 1.5),
          ('Energy price x3', 'energy', 3.0), ('Revenue tax 0 to 20%', 'tax', 0.2)]
rows = []
for sg in SIGMAS:
    p0 = cb.build(sg)
    for (lab, kind, size) in SHOCKS:
        _, _, r = respond(p0, shock_params(p0, kind, size))
        r.update(sigma=sg, shock=lab)
        rows.append(r)
tab = pd.DataFrame(rows)[['shock', 'sigma', 'case', 'exit_zb', 'exit_dp', 'T_zb', 'T_dp', 'dlnX_lr', 'dlnp']]
tab.to_csv(output_path('table_shocks.csv'), index=False)

with open(output_path('table_shocks.tex'), 'w') as fh:
    fh.write('\\begin{tabular}{llccccccc}\n\\toprule\n')
    fh.write(' & & & \\multicolumn{2}{c}{Exit wave at $t=0$} & \\multicolumn{2}{c}{Overhang $T$ (years)} & '
             '\\multicolumn{2}{c}{Long-run change}\\\\\n\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}\n')
    fh.write('Shock & $\\sigma$ & Adjustment & Zero buffer & Deep pocket & Zero buffer & Deep pocket & '
             '$\\Delta\\ln X^*$ & $\\Delta\\ln p^*$\\\\\n\\midrule\n')
    TEXLAB = {'Capability gain (x3)': 'Capability gain ($\\times3$)', 'Energy price +50%': 'Energy price $+50\\%$',
              'Energy price x3': 'Energy price $\\times3$', 'Revenue tax 0 to 20%': 'Revenue tax $0\\to20\\%$'}
    for k, (lab, _, _) in enumerate(SHOCKS):                 # rows grouped by shock, sigma inside each group
        if k > 0:
            fh.write('\\addlinespace\n')
        for sg in SIGMAS:
            r = tab[(tab.shock == lab) & (tab.sigma == sg)].iloc[0]
            first = TEXLAB[lab] if sg == SIGMAS[0] else ''
            fh.write(f"{first} & {sg:.2f} & {r['case']} & {100 * r['exit_zb']:.1f}\\% & {100 * r['exit_dp']:.1f}\\% & "
                     f"{r['T_zb']:.2f} & {r['T_dp']:.2f} & {r['dlnX_lr']:+.3f} & {r['dlnp']:+.3f}\\\\\n")
    fh.write('\\bottomrule\n\\end{tabular}\n')
num['table_shocks'] = tab.to_dict(orient='records')

# ------------------------------------------------------------------ thresholds and long-run distances
c = cb.CAL
al = c['alpha']
psiM0 = c['Omega_M'] / (1 - al)
num['psiM0'] = psiM0
num['psiL0'] = 1 - psiM0
num['sigma_hat_local'] = (1 - psiM0) / (1 - al * psiM0)        # short-run local shakeout threshold
num['sigma_rebound_LR'] = 1 - psiM0                             # long-run compute-rebound threshold
num['sE'] = c['kE_pE'] / (c['delta_X'] + c['kE_pE'])


def spend_change(sg, D):
    p0 = cb.build(sg)
    return np.log(np.exp(D) * em.pM(np.exp(D), p0)) - np.log(em.pM(1.0, p0))


num['sigma_hat_discrete_x3'] = brentq(lambda s: spend_change(s, c['Delta']), 0.5, 0.9999)
dist = {}
for Om in [0.01, 0.02, 0.05]:
    psm = Om / (1 - al)
    for sg in [1.25, 1.5, 2.0, 3.0]:
        lnr = -np.log(psm) / (sg - 1)                           # ln(A_hat/A0)
        dist[f'Om{Om}_sigma{sg}'] = dict(ln_ratio=lnr, ratio=float(np.exp(lnr)), years=lnr / c['g_A'])
num['distance_to_abundance'] = dist
for sg in [1.5, 2.0, 3.0]:
    p0 = cb.build(sg)
    assert abs(np.log(em.critical_capability(p0) / p0['A']) - dist[f'Om0.02_sigma{sg}']['ln_ratio']) < 1e-9

# simultaneous termination after the capability shock (sigma = 0.6)
p0 = cb.build(0.6)
p1 = shock_params(p0, 'capability')
tr = em.transition(p0, p1)
kk = (1 - p1['tau']) * (1 - p1['u']) * p1['x'] * p1['A']
a_pre = p1['Phi'] / (kk * em.pM(np.exp(c['Delta']) * tr['s0']['M'], p1))   # cutoff at the pre-exit price
share_sim = 1 - float(em.tail_mass(a_pre, p1) / em.tail_mass(tr['s0']['a_tilde'], p1))
num['simultaneous_vs_equilibrium_exit_sigma0.6'] = dict(simultaneous=share_sim, equilibrium=tr['exit_share'])

# ------------------------------------------------------------------ sensitivity table
base_cases = [('Capability gain (x3), sigma=0.6', 0.6, 'capability', None),
              ('Revenue tax 0 to 20%, sigma=2.0', 2.0, 'tax', 0.2)]
variations = [('Baseline', {}),
              ('Pareto shape theta=2', dict(theta=2.0)), ('Pareto shape theta=5', dict(theta=5.0)),
              ('Exit hazard 0.25/yr', dict(deltaP=0.25)), ('Exit hazard 1.0/yr', dict(deltaP=1.0)),
              ('Energy cost 0.008', dict(kE_pE=0.008)), ('Energy cost 0.035', dict(kE_pE=0.035)),
              ('Failed-entry share 0.25', dict(fail=0.25)), ('Failed-entry share 0.75', dict(fail=0.75)),
              ('Machine share 0.01', dict(Omega_M=0.01)), ('Machine share 0.05', dict(Omega_M=0.05)),
              ('Depreciation 0.40/yr', dict(delta_X=0.40))]
srows = []
for (clab, sg, kind, size) in base_cases:
    for (vlab, over) in variations:
        p0 = cb.build(sg, **over)
        tr, dp, r = respond(p0, shock_params(p0, kind, size))
        consistent = ((tr['case'] == 'overhang') == (r['dlnX_sr'] < 0)) if kind == 'capability' else (tr['case'] == 'overhang')
        srows.append(dict(experiment=clab, variation=vlab, exit_zb=r['exit_zb'], exit_dp=r['exit_dp'],
                          T_zb=r['T_zb'], T_dp=r['T_dp'], dlnX_lr=r['dlnX_lr'],
                          zb_gt_dp=bool(r['exit_zb'] > r['exit_dp'] + 1e-12), theory_consistent=bool(consistent)))
sens = pd.DataFrame(srows)
sens.to_csv(output_path('table_sensitivity.csv'), index=False)
with open(output_path('table_sensitivity.tex'), 'w') as fh:
    fh.write('\\begin{tabular}{lcccccccc}\n\\toprule\n')
    fh.write(' & \\multicolumn{4}{c}{Capability gain ($\\times3$), $\\sigma=0.6$} & \\multicolumn{4}{c}{Revenue tax $0\\to20\\%$, $\\sigma=2$}\\\\\n'
             '\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}\n')
    fh.write('Variation & Exit ZB & Exit DP & $T$ ZB & $\\Delta\\ln X^*$ & Exit ZB & Exit DP & $T$ ZB & $\\Delta\\ln X^*$\\\\\n\\midrule\n')
    # variations that leave every entry unchanged (with Pareto capability and the initial state normalized they only
    # rescale the cutoff and the price) are reported in the table note rather than as rows; the CSV keeps all of them
    cols = ['exit_zb', 'exit_dp', 'T_zb', 'T_dp', 'dlnX_lr']
    basev = sens[sens.variation == 'Baseline'].set_index('experiment')[cols]
    invariant = [v for (v, _) in variations[1:]
                 if np.allclose(sens[sens.variation == v].set_index('experiment')[cols].values, basev.values,
                                rtol=1e-8, atol=1e-10)]
    num['sensitivity_invariant_variations'] = invariant
    for (vlab, _) in variations:
        if vlab in invariant:
            continue
        a_ = sens[(sens.experiment == base_cases[0][0]) & (sens.variation == vlab)].iloc[0]
        b_ = sens[(sens.experiment == base_cases[1][0]) & (sens.variation == vlab)].iloc[0]
        vtex = vlab.replace('Pareto shape theta=', 'Pareto shape $\\theta=$').replace('/yr', ' per year')
        fh.write(f"{vtex} & {100 * a_.exit_zb:.1f}\\% & {100 * a_.exit_dp:.1f}\\% & {a_.T_zb:.2f} & {a_.dlnX_lr:+.3f} & "
                 f"{100 * b_.exit_zb:.1f}\\% & {100 * b_.exit_dp:.1f}\\% & {b_.T_zb:.2f} & {b_.dlnX_lr:+.3f}\\\\\n")
    fh.write('\\bottomrule\n\\end{tabular}\n')
num['sensitivity_all_zb_gt_dp'] = bool(sens.zb_gt_dp.all())
num['sensitivity_all_theory_consistent'] = bool(sens.theory_consistent.all())
num['sensitivity_ranges'] = {e: dict(exit_zb=[float(sens[sens.experiment == e].exit_zb.min()), float(sens[sens.experiment == e].exit_zb.max())],
                                     exit_dp=[float(sens[sens.experiment == e].exit_dp.min()), float(sens[sens.experiment == e].exit_dp.max())],
                                     ratio=[float((sens[sens.experiment == e].exit_zb / sens[sens.experiment == e].exit_dp).min()),
                                            float((sens[sens.experiment == e].exit_zb / sens[sens.experiment == e].exit_dp).max())])
                             for e in sens.experiment.unique()}

# ------------------------------------------------------------------ Table 1: calibration
cal_rows = [
    ('Capital elasticity of output', '$\\alpha$', '0.38', 'Anchor', 'Labor share 0.597 (PWT 10.01) with $\\Omega_M=0.02$'),
    ('Initial machine-service share of output', '$\\Omega_M$', '0.02', 'Illustrative', 'No official statistic; range 0.01--0.05'),
    ('Elasticity of substitution', '$\\sigma$', '0.6, 0.95, 2.0', 'Illustrative', 'No direct estimate; analogues 0--2.6'),
    ('Compute replacement rate', '$\\delta_X$', '0.20/yr', 'Anchor', '5--6 year useful lives; range 0.17--0.40'),
    ('Energy cost per unit of compute', '$\\kappa_Ep_E$', '0.016/yr', 'Anchor', 'Implies energy share $s_E=0.074$ (direct estimates 0.07--0.09)'),
    ('Exogenous termination hazard', '$\\delta_P$', '0.5/yr', 'Anchor', 'Model-retirement hazards; range 0.25--1.0'),
    ('Capability shock', '$\\Delta$', '$\\ln 3$', 'Anchor', 'About one year of algorithmic progress'),
    ('Growth of capability per unit of compute', '$g_A$', '1.0/yr', 'Anchor', 'Effective-compute doubling 8.4 months'),
    ('Pareto shape of entrant capability', '$\\theta$', '3', 'Illustrative', 'Range 2--5 in Table~\\ref{tab:sensitivity}'),
    ('Share of entrants that never operate', '$\\tilde G(\\tilde a^*)$', '0.5', 'Illustrative', 'Pins $f_e/\\Phi$; range 0.25--0.75'),
    ('Discount rate', '$r$', '0.04', 'Illustrative', ''),
    ('Depreciation of conventional capital', '$\\delta_K$', '0.06', 'Illustrative', 'Enters only through $y_K=(r+\\delta_K)/\\alpha$'),
]
with open(output_path('table_calibration.tex'), 'w') as fh:
    fh.write('\\begin{tabular}{p{5.2cm}ccp{1.6cm}p{5.4cm}}\n\\toprule\nParameter & Symbol & Value & Use & Source or note\\\\\n\\midrule\n')
    for r_ in cal_rows:
        fh.write(' & '.join(r_) + '\\\\\n')
    fh.write('\\bottomrule\n\\end{tabular}\n')

# ------------------------------------------------------------------ Figure 1: long-run regime map
fig, ax = plt.subplots(figsize=(4.6, 3.3))
sg_lo = np.linspace(0.25, 0.995, 400)
sg_hi = np.linspace(1.005, 3.0, 400)
ln10 = np.log(10)
for Om, lw, col, alpha_ in [(0.01, 0.8, C_GREY, 0.9), (0.05, 0.8, C_GREY, 0.9), (0.02, 1.8, 'k', 1.0)]:
    psm = Om / (1 - al)
    ylo = np.log(psm) / (1 - sg_lo) / ln10
    yhi = -np.log(psm) / (sg_hi - 1) / ln10
    ax.plot(sg_lo, ylo, color=col, lw=lw, alpha=alpha_)
    ax.plot(sg_hi, yhi, color=col, lw=lw, alpha=alpha_)
psm = c['Omega_M'] / (1 - al)
ylo = np.log(psm) / (1 - sg_lo) / ln10
yhi = -np.log(psm) / (sg_hi - 1) / ln10
YMIN, YMAX = -4.0, 4.0
ax.fill_between(sg_lo, YMIN, np.clip(ylo, YMIN, YMAX), color=C_COMP, alpha=0.13, lw=0)
ax.fill_between(sg_hi, np.clip(yhi, YMIN, YMAX), YMAX, color=C_SUBS, alpha=0.13, lw=0)
ax.axhline(0, color=C_GREY, lw=0.8, ls=':')
ax.axvline(1, color=C_GREY, lw=0.6)
ax.set_xlim(0.25, 3.0)
ax.set_ylim(YMIN, YMAX)
ax.set_xlabel('Elasticity of substitution between labor and machine services, $\\sigma$')
ax.set_ylabel('Capability relative to today, $A/A_0$')
ax.set_yticks([-4, -2, 0, 2, 4])
ax.set_yticklabels(['$10^{-4}$', '$10^{-2}$', '$1$', '$10^{2}$', '$10^{4}$'])
ax.text(0.28, -3.85, 'not\nviable', color=C_COMP, fontsize=7, va='bottom')
ax.text(0.29, 2.6, 'viable, finite\nmachine sector', color='k', fontsize=7)
ax.text(1.70, 3.05, 'unbounded machine\nexpansion', color=C_SUBS, fontsize=7)
ax.text(1.55, -2.6, 'finite machine sector', color='k', fontsize=7)
ax.text(0.40, 0.12, 'today', color=C_GREY, fontsize=7)
xa = 2.2
ax.annotate('critical capability $\\hat A$', xy=(xa, -np.log(psm) / (xa - 1) / ln10), xytext=(1.50, 0.38), fontsize=7,
            arrowprops=dict(arrowstyle='->', color='k', lw=0.6, shrinkA=1.5, shrinkB=1.5))
sec = ax.secondary_yaxis('right', functions=(lambda y: y * ln10 / c['g_A'], lambda yy: yy * c['g_A'] / ln10))
sec.set_ylabel('Years of capability growth at $g_A=1$')
fig.tight_layout()
fig.savefig(output_path('fig1_regimes.pdf')); fig.savefig(output_path('fig1_regimes.png'), dpi=300)
plt.close(fig)

# ------------------------------------------------------------------ Figure 2: compute and labor share vs capability
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.8))
Agrid = np.exp(np.linspace(0.0, np.log(100.0), 600))
series = [(0.6, C_COMP, '-'), (0.95, C_NEAR, '-'), (1.0, 'k', '-'), (1.5, '#e08a4f', '-'), (2.0, C_SUBS, '-')]
for sg, col, ls in series:
    p0 = cb.build(sg)
    X0 = em.stationary_LR(p0)['X']
    Xs, sL = [], []
    for Ar in Agrid:
        s = em.stationary_LR(p0, A=p0['A'] * Ar)
        if s['regime'] != 'finite':
            Xs.append(np.nan); sL.append(np.nan); continue
        Xs.append(s['X'] / X0); sL.append((1 - al) * s['psiL'])
    Xs, sL = np.array(Xs), np.array(sL)
    axs[0].plot(Agrid, Xs, color=col, ls=ls, lw=1.4)
    axs[1].plot(Agrid, sL, color=col, ls=ls, lw=1.4)
    i_last = np.where(np.isfinite(Xs))[0][-1]
    if sg == 2.0:
        axs[0].text(Agrid[i_last] * 0.62, 70, '$\\sigma=2$', color=col, fontsize=7, va='center', ha='right')
        axs[1].text(Agrid[i_last] * 0.85, 0.05, '$\\sigma=2$', color=col, fontsize=7, va='center', ha='right')
    else:
        yoff = {0.95: 0.82, 1.0: 1.22}.get(sg, 1.0)
        axs[0].text(105, Xs[i_last] * yoff, f'$\\sigma={sg:g}$', color=col, fontsize=7, va='center')
    if sg == 1.5:
        axs[1].text(105, sL[i_last], '$\\sigma=1.5$', color=col, fontsize=7, va='center')
axs[1].text(105, 0.63, '$\\sigma\\leq1$', color=C_COMP, fontsize=7, va='center')
Ah2 = dist['Om0.02_sigma2.0']['ratio']
for ax_ in axs:
    ax_.axvline(Ah2, color=C_SUBS, lw=0.6, ls=':')
axs[1].text(Ah2 * 1.06, 0.33, 'critical capability\nfor $\\sigma=2$', color=C_SUBS, fontsize=6, va='center')
axs[0].set_xscale('log'); axs[0].set_yscale('log')
axs[0].set_ylim(0.1, 100)
axs[0].set_xlabel('Capability relative to today, $A/A_0$')
axs[0].set_ylabel('Long-run compute, $X^*/X^*_0$')
axs[0].set_title('Capability saves compute\nonly under complementarity', loc='left')
axs[1].set_xscale('log')
axs[1].set_xlabel('Capability relative to today, $A/A_0$')
axs[1].set_ylabel('Long-run labor share, $s_L^*$')
axs[1].set_title('The labor share falls\nonly under substitution', loc='left')
for ax_ in axs:
    ax_.set_xlim(1, 100)
    ax_.set_xticks([1, 10, 100]); ax_.set_xticklabels(['1', '10', '100'])
axs[0].set_yticks([0.1, 1, 10, 100]); axs[0].set_yticklabels(['0.1', '1', '10', '100'])
_panel_letter(axs[0], 'a'); _panel_letter(axs[1], 'b')
fig.tight_layout(w_pad=5.0)
fig.savefig(output_path('fig2_compute.pdf')); fig.savefig(output_path('fig2_compute.png'), dpi=300)
plt.close(fig)

# ------------------------------------------------------------------ Figure 3: transitions
fig, axs = plt.subplots(2, 2, figsize=(6.8, 4.6), sharex='col')
tt = np.linspace(-0.25, 2.0, 901)
for col_i, (kind, size, title) in enumerate([('capability', None, 'Capability gain ($\\times3$)'),
                                              ('tax', 0.2, 'Revenue tax $0\\to20\\%$')]):
    for sg, col in [(0.6, C_COMP), (2.0, C_SUBS)]:
        p0 = cb.build(sg); p1 = shock_params(p0, kind, size)
        tr = em.transition(p0, p1, horizon=2.0, npts=4001)
        paths = [('zero buffer', tr, '-')]
        if tr['case'] == 'overhang':
            paths.append(('deep pocket', em.deep_pocket_path(p0, p1, horizon=2.0, npts=4001), '--'))
        for lab, pth, ls in paths:
            n_ = np.interp(np.clip(tt, 0, None), pth['t'], pth['n'] / tr['s0']['n'])
            n_ = np.where(tt < 0, 1.0, n_)
            pr = np.interp(np.clip(tt, 0, None), pth['t'], pth['price'] / tr['s0']['price'])
            pr = np.where(tt < 0, 1.0, pr)
            axs[0, col_i].plot(tt, n_, color=col, ls=ls, lw=1.3)
            axs[1, col_i].plot(tt, pr, color=col, ls=ls, lw=1.3)
    axs[0, col_i].set_title(title, loc='left')
    axs[1, col_i].set_xlabel('Years after the shock')
    for r_ in range(2):
        axs[r_, col_i].axvline(0, color=C_GREY, lw=0.6, ls=':')
axs[0, 0].set_ylabel('Active providers, $n(t)/n_0$')
axs[1, 0].set_ylabel('Price of machine services, $p(t)/p_0$')
axs[0, 0].text(1.15, 0.74, '$\\sigma=0.6$', color=C_COMP, fontsize=7)
axs[0, 0].text(1.15, 2.55, '$\\sigma=2$', color=C_SUBS, fontsize=7)
axs[0, 0].plot([], [], color='k', ls='-', lw=1.3, label='zero buffer (earn or terminate)')
axs[0, 0].plot([], [], color='k', ls='--', lw=1.3, label='deep pocket')
axs[0, 0].legend(loc='center right', bbox_to_anchor=(1.0, 0.52))
axs[0, 1].text(1.55, 0.875, '$\\sigma=0.6$', color=C_COMP, fontsize=7)
axs[0, 1].text(1.55, 0.635, '$\\sigma=2$', color=C_SUBS, fontsize=7)
for ax_, l_ in zip(axs.flat, 'abcd'):
    _panel_letter(ax_, l_)
fig.tight_layout()
fig.savefig(output_path('fig3_transition.pdf')); fig.savefig(output_path('fig3_transition.png'), dpi=300)
plt.close(fig)

# ------------------------------------------------------------------ Figure 4: sensitivity of shakeouts to sigma
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.8))
sgrid = np.linspace(0.3, 1.2, 181)
for th, lw in [(2.0, 0.8), (3.0, 1.6), (5.0, 0.8)]:
    ez, ed = [], []
    for sg in sgrid:
        p0 = cb.build(sg, theta=th); p1 = shock_params(p0, 'capability')
        _, _, r = respond(p0, p1)
        ez.append(r['exit_zb']); ed.append(r['exit_dp'])
    axs[0].plot(sgrid, 100 * np.array(ez), color=C_COMP, lw=lw)
    axs[0].plot(sgrid, 100 * np.array(ed), color=C_COMP, lw=lw, ls='--')
axs[0].axvline(num['sigma_hat_discrete_x3'], color=C_GREY, lw=0.6, ls=':')
axs[0].set_xlabel('Elasticity of substitution, $\\sigma$')
axs[0].set_ylabel('Incumbents terminated at $t=0$ (%)')
axs[0].set_title('Capability gains terminate providers\nonly under complementarity', loc='left')
axs[0].plot([], [], color=C_COMP, ls='-', label='zero buffer'); axs[0].plot([], [], color=C_COMP, ls='--', label='deep pocket')
axs[0].legend(loc='upper right')
for D, lw, lab in [(np.log(2.0), 0.8, '$\\times2$'), (np.log(3.0), 1.6, '$\\times3$'), (np.log(10.0), 0.8, '$\\times10$')]:
    dx = []
    for sg in sgrid:
        p0 = cb.build(sg); p1 = shock_params(p0, 'capability', D)
        s0L, s1L = em.stationary_LR(p0), em.stationary_LR(p1)
        dx.append(np.log(s1L['X'] / s0L['X']) if s1L['regime'] == 'finite' else np.nan)
    axs[1].plot(sgrid, dx, color='k', lw=lw)
    axs[1].text(1.205, dx[-1] + {'$\\times2$': -0.05, '$\\times3$': 0.05}.get(lab, 0.0), lab, fontsize=6, va='center')
axs[1].axhline(0, color=C_GREY, lw=0.6)
axs[1].axvline(num['sigma_rebound_LR'], color=C_GREY, lw=0.6, ls=':')
axs[1].set_xlabel('Elasticity of substitution, $\\sigma$')
axs[1].set_ylabel('$\\Delta\\ln X^*$ (long-run compute)')
axs[1].set_title('Compute rebounds once $\\sigma$\nexceeds $s_L/(1-\\alpha)$', loc='left')
_panel_letter(axs[0], 'a'); _panel_letter(axs[1], 'b')
fig.tight_layout(w_pad=4.0)
fig.savefig(output_path('fig4_sensitivity.pdf')); fig.savefig(output_path('fig4_sensitivity.png'), dpi=300)
plt.close(fig)

with open(output_path('numbers.json'), 'w') as fh:
    json.dump(num, fh, indent=1, default=float)
print('done')