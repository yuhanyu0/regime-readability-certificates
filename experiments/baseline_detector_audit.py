from __future__ import annotations
import json, math, os, sys
from pathlib import Path
from typing import Any

os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from scipy.special import logsumexp

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
TAB = OUT / 'tables'
FIG = OUT / 'figures'
CERT = OUT / 'certificates'


def ensure_dirs():
    for p in [TAB, FIG, CERT]: p.mkdir(parents=True, exist_ok=True)


def gaussian_logpdf(x: np.ndarray, mean: float, var: float) -> np.ndarray:
    var = max(float(var), 1e-6)
    return -0.5*(np.log(2*np.pi*var) + (x-mean)**2/var)


def simple_hmm_fit(x: np.ndarray, n_iter: int = 40) -> dict[str, Any]:
    x = np.asarray(x, dtype=float).reshape(-1)
    n = len(x)
    if n < 20 or np.std(x) < 1e-10:
        return {'detected': False, 'delta_BIC': np.nan, 'n_switches': 0, 'state_share_min': 0.0}
    qs = np.quantile(x, [0.33, 0.67])
    means = np.array([qs[0], qs[1]], dtype=float)
    vars_ = np.array([np.var(x), np.var(x)], dtype=float) + 1e-4
    A = np.array([[0.96, 0.04], [0.04, 0.96]], dtype=float)
    pi = np.array([0.5, 0.5], dtype=float)
    for _ in range(n_iter):
        logB = np.vstack([gaussian_logpdf(x, means[k], vars_[k]) for k in range(2)]).T
        logA = np.log(A + 1e-12)
        logpi = np.log(pi + 1e-12)
        alpha = np.zeros((n,2)); alpha[0] = logpi + logB[0]
        for t in range(1,n):
            alpha[t] = logB[t] + logsumexp(alpha[t-1][:,None] + logA, axis=0)
        ll = logsumexp(alpha[-1])
        beta = np.zeros((n,2))
        for t in range(n-2,-1,-1):
            beta[t] = logsumexp(logA + logB[t+1][None,:] + beta[t+1][None,:], axis=1)
        gamma = np.exp(alpha + beta - ll)
        xi_sum = np.zeros((2,2))
        for t in range(n-1):
            tmp = alpha[t][:,None] + logA + logB[t+1][None,:] + beta[t+1][None,:] - ll
            xi_sum += np.exp(tmp)
        pi = gamma[0] / gamma[0].sum()
        A = xi_sum / np.maximum(xi_sum.sum(axis=1, keepdims=True), 1e-12)
        weights = gamma.sum(axis=0)
        means = (gamma * x[:,None]).sum(axis=0) / np.maximum(weights, 1e-12)
        vars_ = (gamma * (x[:,None]-means[None,:])**2).sum(axis=0) / np.maximum(weights, 1e-12) + 1e-6
    logB = np.vstack([gaussian_logpdf(x, means[k], vars_[k]) for k in range(2)]).T
    logA = np.log(A + 1e-12)
    logpi = np.log(pi + 1e-12)
    delta = np.zeros((n,2)); psi = np.zeros((n,2), dtype=int)
    delta[0] = logpi + logB[0]
    for t in range(1,n):
        vals = delta[t-1][:,None] + logA
        psi[t] = np.argmax(vals, axis=0)
        delta[t] = logB[t] + np.max(vals, axis=0)
    states = np.zeros(n, dtype=int); states[-1] = int(np.argmax(delta[-1]))
    for t in range(n-2,-1,-1): states[t] = psi[t+1, states[t+1]]
    counts = np.bincount(states, minlength=2)
    min_share = counts.min()/n
    n_switches = int(np.sum(states[1:] != states[:-1]))
    loglike2 = float(logsumexp(alpha[-1]))
    mu = float(np.mean(x)); var = float(np.var(x)+1e-6)
    loglike1 = float(np.sum(gaussian_logpdf(x, mu, var)))
    bic1 = -2*loglike1 + 2*np.log(n)
    bic2 = -2*loglike2 + 7*np.log(n)
    delta_bic = float(bic1 - bic2)
    detected = bool(delta_bic > 10 and min_share >= 0.10)
    return {'detected': detected, 'delta_BIC': delta_bic, 'n_switches': n_switches, 'state_share_min': float(min_share)}


def gmm_detector(x: np.ndarray) -> dict[str, Any]:
    x = np.asarray(x, dtype=float).reshape(-1,1)
    n = len(x)
    if n < 20 or np.std(x) < 1e-10:
        return {'detected': False, 'delta_BIC': np.nan, 'min_component_frac': 0.0}
    g1 = GaussianMixture(1, random_state=11, n_init=5, max_iter=100, reg_covar=1e-6).fit(x)
    g2 = GaussianMixture(2, random_state=11, n_init=5, max_iter=100, reg_covar=1e-6).fit(x)
    labels = g2.predict(x)
    counts = np.bincount(labels, minlength=2)
    min_frac = counts.min()/n
    delta = float(g1.bic(x)-g2.bic(x))
    return {'detected': bool(delta > 10 and min_frac >= 0.10), 'delta_BIC': delta, 'min_component_frac': float(min_frac)}


def changepoint_detector(x: np.ndarray) -> dict[str, Any]:
    x = np.asarray(x, dtype=float).reshape(-1)
    n=len(x)
    if n < 30:
        return {'detected': False, 'delta_BIC': np.nan, 'cp_index': None}
    sse0 = np.sum((x-x.mean())**2)
    best = (np.inf, None)
    for t in range(max(10, n//10), min(n-10, 9*n//10)):
        left, right = x[:t], x[t:]
        sse = np.sum((left-left.mean())**2) + np.sum((right-right.mean())**2)
        if sse < best[0]: best=(sse,t)
    bic0 = n*np.log(max(sse0/n,1e-9)) + 2*np.log(n)
    bic1 = n*np.log(max(best[0]/n,1e-9)) + 4*np.log(n)
    delta = float(bic0-bic1)
    return {'detected': bool(delta > 10), 'delta_BIC': delta, 'cp_index': int(best[1]) if best[1] is not None else None}


def threshold_detector(x: np.ndarray) -> dict[str, Any]:
    x = np.asarray(x, dtype=float).reshape(-1)
    if len(x) < 20 or np.std(x) < 1e-10:
        return {'detected': False, 'separation_z': 0.0, 'high_share': 0.0}
    z = (x-np.mean(x))/(np.std(x)+1e-9)
    high = z > 0.75
    high_share = high.mean()
    sep = float(z[high].mean()-z[~high].mean()) if high.any() and (~high).any() else 0.0
    return {'detected': bool(0.10 <= high_share <= 0.90 and sep > 1.2), 'separation_z': sep, 'high_share': float(high_share)}


def generate_worlds(n: int = 800, seed: int = 1601) -> dict[str, dict[str, Any]]:
    rng = np.random.default_rng(seed)
    latent = np.r_[np.zeros(n//2, dtype=int), np.ones(n-n//2, dtype=int)]
    manifest = rng.normal(0,1,n)
    audit = latent + 0.25*rng.normal(size=n)
    worlds = {
        'hidden_supported': {
            'series': manifest,
            'audit_series': audit,
            'latent_support': True,
            'rrc': {'readability_status': 'hidden', 'support_scope': 'oracle_asserted', 'persistence_status': 'not_tested', 'selection_status': 'not_applicable'},
            'expected_failure': 'weak interface hides an oracle-supported split',
        }
    }
    comps = rng.binomial(1, 0.5, size=n)
    phantom = rng.normal(np.where(comps==1, 1.75, -1.75), 0.45)
    worlds['surface_phantom'] = {
        'series': phantom,
        'latent_support': False,
        'rrc': {'readability_status': 'phantom', 'support_scope': 'support_rejected', 'persistence_status': 'unstable', 'selection_status': 'not_applicable'},
        'expected_failure': 'visible separation without generator support',
    }
    states=[]; cur=0
    while len(states)<n:
        L=int(rng.integers(25,55)); states.extend([cur]*L); cur=1-cur
    states=np.array(states[:n])
    switch_series = rng.normal(np.where(states==1, 1.25, -1.25), 0.6)
    coarse = switch_series[::45]
    worlds['coarse_stride_switching'] = {
        'series': coarse,
        'latent_support': True,
        'rrc': {'readability_status': 'not_identifiable', 'support_scope': 'oracle_asserted', 'persistence_status': 'not_identifiable', 'selection_status': 'not_applicable'},
        'expected_failure': 'coarse stride leaves too few transition opportunities',
    }
    t=np.linspace(0,1,n)
    rho=0.2+0.55/(1+np.exp(-12*(t-0.55)))+0.04*rng.normal(size=n)
    ipr=0.13+0.008*np.sin(10*np.pi*t)+0.003*rng.normal(size=n)
    worlds['occupancy_migration'] = {
        'series': rho,
        'aux_series': ipr,
        'latent_support': False,
        'rrc': {'readability_status': 'identified', 'support_scope': 'not_asserted', 'persistence_status': 'not_tested', 'selection_status': 'not_applicable'},
        'expected_failure': 'regime-change readout is migration across phase space, not fixed-slice switching',
    }
    stable = rng.normal(0,1,n)
    worlds['stable_null'] = {
        'series': stable,
        'latent_support': False,
        'rrc': {'readability_status': 'not_identifiable', 'support_scope': 'support_rejected', 'persistence_status': 'not_tested', 'selection_status': 'not_applicable'},
        'expected_failure': 'low signal should not be promoted',
    }
    return worlds


def main():
    ensure_dirs()
    worlds = generate_worlds()
    rows=[]
    for name,w in worlds.items():
        x=np.asarray(w['series'], dtype=float)
        dets={
            'GMM': gmm_detector(x),
            'HMM': simple_hmm_fit(x),
            'change_point': changepoint_detector(x),
            'threshold': threshold_detector(x),
        }
        for det_name, res in dets.items():
            rows.append({
                'world': name,
                'detector': det_name,
                'detector_detected': bool(res.get('detected', False)),
                'detector_delta_BIC': res.get('delta_BIC', np.nan),
                'detector_metric': res.get('separation_z', res.get('min_component_frac', np.nan)),
                'readability_status': w['rrc']['readability_status'],
                'support_scope': w['rrc']['support_scope'],
                'persistence_status': w['rrc']['persistence_status'],
                'selection_status': w['rrc']['selection_status'],
                'audit_interpretation': w['expected_failure'],
            })
    df=pd.DataFrame(rows)
    df.to_csv(TAB/'baseline_detector_experiment_v1_6.csv', index=False)
    piv=df.pivot_table(index='world', columns='detector', values='detector_detected', aggfunc='first')
    rrc=pd.DataFrame([{'world':k, **w['rrc'], 'interpretation':w['expected_failure']} for k,w in worlds.items()]).set_index('world')
    out=piv.join(rrc).reset_index()
    out.to_csv(TAB/'baseline_detector_experiment_summary_v1_6.csv', index=False)
    cert={
        'certificate_id':'baseline_detector_experiment_v1_6',
        'claim_type':'detector_output_audit_benchmark',
        'protocol':'same synthetic worlds; manifest channel unless otherwise specified; detector outputs audited by RRC four-field grammar',
        'detectors':['GMM','HMM','change_point','threshold'],
        'worlds':list(worlds.keys()),
        'evidence':{
            'n_worlds':len(worlds),
            'n_detector_world_pairs':len(df),
            'detector_positive_counts':df.groupby('detector')['detector_detected'].sum().astype(int).to_dict(),
            'rrc_status_counts':out['readability_status'].value_counts().to_dict(),
        },
        'interpretation':[
            'Conventional detector output is not a valid regime claim by itself.',
            'The same detected/non-detected output can be reclassified as hidden, phantom, not_identifiable, or identified migration audit depending on support scope and protocol.',
        ]
    }
    (CERT/'baseline_detector_experiment_certificate_v1_6.json').write_text(json.dumps(cert,indent=2), encoding='utf-8')
    fig, axes = plt.subplots(1,2,figsize=(11.5,4.2), gridspec_kw={'width_ratios':[1.25,1.75]})
    det_order=['GMM','HMM','change_point','threshold']
    world_order=['hidden_supported','surface_phantom','coarse_stride_switching','occupancy_migration','stable_null']
    mat=np.array([[bool(piv.loc[w,d]) if (w in piv.index and d in piv.columns) else False for d in det_order] for w in world_order], dtype=int)
    ax=axes[0]
    ax.imshow(mat, cmap='Greys', vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(len(det_order))); ax.set_xticklabels(det_order, rotation=35, ha='right')
    ax.set_yticks(range(len(world_order))); ax.set_yticklabels([w.replace('_',' ') for w in world_order])
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j,i,'yes' if mat[i,j] else 'no',ha='center',va='center',color='white' if mat[i,j] else 'black',fontsize=8)
    ax.set_title('Conventional detector says regime?')
    ax2=axes[1]; ax2.axis('off')
    color_map={'identified':'#1b9e77','hidden':'#7570b3','phantom':'#d95f02','not_identifiable':'#999999','rejected':'#e7298a'}
    y=0.95
    ax2.text(0.0,y,'RRC certificate reclassifies the detector output',fontsize=11,fontweight='bold',transform=ax2.transAxes); y-=0.10
    for w in world_order:
        rr=rrc.loc[w]
        c=color_map.get(rr['readability_status'],'#666666')
        ax2.add_patch(plt.Rectangle((0.0,y-0.035),0.035,0.035,color=c,transform=ax2.transAxes,clip_on=False))
        ax2.text(0.05,y,w.replace('_',' '),fontsize=9,fontweight='bold',transform=ax2.transAxes,va='center')
        ax2.text(0.37,y,f"readability={rr['readability_status']}; support={rr['support_scope']}",fontsize=8,transform=ax2.transAxes,va='center')
        ax2.text(0.05,y-0.045,rr['interpretation'],fontsize=7.5,transform=ax2.transAxes,va='center')
        y-=0.16
    fig.tight_layout()
    fig.savefig(FIG/'fig_baseline_detector_experiment_v1_6.png', dpi=240, bbox_inches='tight')
    plt.close(fig)
    print(json.dumps({'rows':len(df),'outputs':['baseline_detector_experiment_v1_6.csv','fig_baseline_detector_experiment_v1_6.png']},indent=2))

if __name__=='__main__':
    main()
