# -*- coding: utf-8 -*-
"""S1 — RS 补充材料实验(population-restricted 压力工作点)
设计: S1 场景, SN=6 (low-parallelism 部署形态), 等预算 6600 evals
      (cycles=500 由 cycles_for_budget 换算), limit=40 不动, tuned 参数不动
      full vs w/o RS, seeds 5000-5049 各 50 runs
统计: Best/Mean±SD/ΔF̄(paired bootstrap 95% CI)/Wilcoxon raw p/Holm p/触发计数
输出: data/revision/rs_activation_stress.json + 控制台表格
"""
import sys, io, json, time, math
from pathlib import Path

ROOT = Path(r'C:/Project/SHDMS-ABC/ABC_Research/github-content')
sys.path.insert(0, str(ROOT / 'experiments'))
from common.paths import ensure_import_paths
ensure_import_paths()

from common.model import build_dataset_model, create_scenario_model
from common.runtime import VariantSHDMSABC, build_shdms_config
from common.statistics import wilcoxon_signed_rank, holm_adjust

import numpy as np
import algorithm  # bridge
from shdms_abc_suite.optimizer import SHDMSArtificialBeeColony  # type: ignore

orig_scout = SHDMSArtificialBeeColony._scout_bee_phase

def counting_scout(self, cycle, metrics, csc, csg):
    ex = np.where(self.trial_counters >= self.config.limit)[0]
    if len(ex):
        self._restart_events = getattr(self, '_restart_events', 0) + len(ex)
    return orig_scout(self, cycle, metrics, csc, csg)

SHDMSArtificialBeeColony._scout_bee_phase = counting_scout

# ---------- 配置(协议与 Table 15 完全一致, 仅 SN 压缩) ----------
SN = 6
LIMIT = 40
BUDGET = 6600
CYCLES = max(1, round((BUDGET - SN) / (2.0 * SN + 1.2)))
SEEDS = list(range(5000, 5050))
VARIANTS = ['SHDMS-ABC', 'w/o RS']

model = build_dataset_model('NST-HSR')
sm = create_scenario_model(model, 'S1')

out = {'protocol': 'S1, SN=6 low-parallelism operating point, budget 6600 evals, '
                   'limit 40 (unchanged), tuned parameters, seeds 5000-5049',
       'SN': SN, 'cycles': CYCLES, 'limit': LIMIT, 'budget': BUDGET,
       'variants': {}, 'statistics': {}}

runs_data = {}
for variant in VARIANTS:
    rows = []
    t0 = time.time()
    for seed in SEEDS:
        cfg = build_shdms_config(SN, CYCLES, LIMIT, seed)
        opt = VariantSHDMSABC(sm.objective, sm.bounds(), cfg,
                              seed_solutions=sm.seed_solutions(),
                              variant=variant)
        res = opt.optimize()
        rows.append({'seed': seed, 'best': float(res.best_value),
                     'evals': int(res.evaluations),
                     'restarts': int(getattr(opt, '_restart_events', 0))})
    runs_data[variant] = rows
    vals = [r['best'] for r in rows]
    rs_counts = [r['restarts'] for r in rows]
    out['variants'][variant] = {
        'mean': float(np.mean(vals)), 'std': float(np.std(vals, ddof=1)),
        'best': float(np.min(vals)), 'worst': float(np.max(vals)),
        'restarts_mean': float(np.mean(rs_counts)),
        'restarts_total': int(sum(rs_counts)),
        'restart_triggered_runs': int(sum(1 for c in rs_counts if c > 0)),
        'runtime_mean_s': round((time.time() - t0) / len(rows), 2),
    }
    print(f'{variant}: mean={np.mean(vals):.4f} ± {np.std(vals, ddof=1):.4f} '
          f'best={np.min(vals):.4f} '
          f'restart_runs={sum(1 for c in rs_counts if c > 0)}/50 '
          f'(total {sum(rs_counts)}, mean {np.mean(rs_counts):.1f}) '
          f'[{time.time()-t0:.0f}s]', flush=True)

# ---------- 统计: 配对 bootstrap CI + Wilcoxon + Holm ----------
ref = [r['best'] for r in runs_data['SHDMS-ABC']]
for variant in VARIANTS[1:]:
    var_vals = [r['best'] for r in runs_data[variant]]
    diff = np.array(var_vals) - np.array(ref)
    mean_diff = float(np.mean(diff))
    # paired bootstrap 95% CI (10,000 resamples, seed 固定可复现)
    rng = np.random.default_rng(2026)
    n = len(diff)
    boot = np.array([np.mean(diff[rng.integers(0, n, n)]) for _ in range(10000)])
    ci = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
    # Wilcoxon signed-rank
    try:
        w_stat, w_p = wilcoxon_signed_rank(ref, var_vals)
    except Exception as e:
        w_stat, w_p = None, str(e)
    out['statistics'][variant] = {
        'mean_diff': mean_diff, 'boot95_mean_diff': ci,
        'wilcoxon_p': (float(w_p) if w_p is not None else None),
        'wilcoxon_stat': (float(w_stat) if w_stat is not None else None),
    }
    print(f'{variant}: ΔF̄={mean_diff:.4f} CI[{ci[0]:.4f},{ci[1]:.4f}] '
          f'wilcoxon_p={w_p}', flush=True)

# Holm 校正(两变体族: w/o SH/w/o PS 已在 Table 15, 此处单对照族 w/o RS)
holm = holm_adjust({'w/o RS': out['statistics']['w/o RS']['wilcoxon_p']})
out['statistics']['w/o RS']['holm_p'] = float(list(holm.values())[0])
print(f'Holm-adjusted p (single contrast) = {list(holm.values())[0]}', flush=True)

out['runs_detail'] = runs_data

out_path = ROOT / 'data' / 'revision' / 'rs_activation_stress.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print('saved ->', out_path)
