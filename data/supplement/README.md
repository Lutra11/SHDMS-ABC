# Supplement: revision experiment data

CSV-only packages holding the revision experiments. Every file is UTF-8 CSV with a BOM and CRLF line endings. The AFC/MLA/SA/FC prefixes are package-internal; they do not correspond to manuscript table or experiment numbering.

| Folder | Prefix | Aspect | Manuscript anchor |
|---|---|---|---|
| [1.Algorithm-level fair comparison](1.Algorithm-level%20fair%20comparison) | AFC | algorithm-level comparison under the unified protocol | Tables 6, 12, 20 |
| [2.Mechanism-level attribution](2.Mechanism-level%20attribution) | MLA | mechanism attribution: 2x2 factorial ablation and restart-scout stress tests | Table 15 |
| [3.Sensitivity analysis](3.Sensitivity%20analysis) | SA | demand sensitivity of the optimized plan | Table 13 |
| [4.Forced control](4.Forced%20control) | FC | forced-activation control on the restart limit | Table 14 (L_R rows) |

## Conventions

- Ablation contrasts use 50 paired seeds (5000–5049) per variant; the fair comparison uses 30 runs per algorithm per scenario; the demand sweep uses 30 runs per level.
- Strict-budget runs use exactly 6,600 objective evaluations. The historical stress test (MLA-11–13) recorded 9,406–9,413 evaluations per run and is retained only as a superseded record.
- Differences are variant minus complete; positive values favour the complete algorithm.
- Wilcoxon tests are two-sided exact sign-permutation signed-rank tests; bootstrap 95% CIs use 100,000 resamples; Holm adjustment is applied over the 12 primary factorial contrasts.
- The factorial and restart-scout stress experiments are produced by `experiments/4-14_factorial_ablation.py` and `experiments/4-15_rs_stress_strict.py` in this repository.

## 1.Algorithm-level fair comparison

| CSV | Rows | Content |
|---|---|---|
| [AFC-1.csv](1.Algorithm-level%20fair%20comparison/AFC-1.csv) | 36 | Unified-protocol re-run: 9 algorithms x 4 scenarios, 30 runs each; `mean_evals` reports each algorithm's natural evaluation count (Table 12) |
| [AFC-2.csv](1.Algorithm-level%20fair%20comparison/AFC-2.csv) | 20 | Equal-budget control: SHDMS-ABC truncated to the 2,904 evaluations at which the four baselines terminate, vs PSO/DE/GWO/HHO (4 scenarios x 30 runs each) |
| [AFC-3.csv](1.Algorithm-level%20fair%20comparison/AFC-3.csv) | 8 | Cross-line deployment, four external lines, reference vs optimized (reference = each line's timetable plan; optimized = 30-run mean; Table 20, external-line rows) |
| [AFC-4.csv](1.Algorithm-level%20fair%20comparison/AFC-4.csv) | 2 | Passenger perspective: original timetable vs the optimized 57-service plan (Tables 7–8; Table 20 NST-HSR row) |
| [AFC-5.csv](1.Algorithm-level%20fair%20comparison/AFC-5.csv) | 3 | Ex-post constraint-violation audit: original plan, best-of-30 SHDMS-ABC plan, published Table 7 plan (Table 6) |

## 2.Mechanism-level attribution

Current chain (Table 15):

| CSV | Rows | Content |
|---|---|---|
| [MLA-1.csv](2.Mechanism-level%20attribution/MLA-1.csv) | 800 | 2x2 factorial ablation per-run records: 4 variants x S1–S4 x 50 paired seeds, exactly 6,600 evaluations per run (Table 15a) |
| [MLA-2.csv](2.Mechanism-level%20attribution/MLA-2.csv) | 16 | Factorial variant summary: mean, SD, best, RS-triggered runs per scenario and variant |
| [MLA-3.csv](2.Mechanism-level%20attribution/MLA-3.csv) | 16 | Factorial contrasts: 12 variant-minus-complete comparisons (Holm family) + 4 interaction contrasts I |
| [MLA-4.csv](2.Mechanism-level%20attribution/MLA-4.csv) | 100 | Restart-scout stress, activation arm (population 4, 3,300-cycle ceiling): per-run records; 45/50 runs trigger |
| [MLA-5.csv](2.Mechanism-level%20attribution/MLA-5.csv) | 100 | Restart-scout stress, ceiling arm (population 6): per-run records; 0/50 runs trigger within the budget |
| [MLA-6.csv](2.Mechanism-level%20attribution/MLA-6.csv) | 4 | Two-arm variant summary: trigger counts, restart totals, trial-counter ranges |
| [MLA-7.csv](2.Mechanism-level%20attribution/MLA-7.csv) | 2 | Two-arm paired statistics: mean difference, bootstrap CI, Wilcoxon p, win/loss/tie counts |

Superseded records (kept for provenance):

| CSV | Rows | Content |
|---|---|---|
| [MLA-8.csv](2.Mechanism-level%20attribution/MLA-8.csv) | 200 | First seed-matched ablation (base scenario, 4 variants incl. a standard-condition no-directed-scout arm); superseded as the Table 15 basis by MLA-1–3 |
| [MLA-9.csv](2.Mechanism-level%20attribution/MLA-9.csv) | 4 | Its variant summary |
| [MLA-10.csv](2.Mechanism-level%20attribution/MLA-10.csv) | 3 | Its contrasts |
| [MLA-11.csv](2.Mechanism-level%20attribution/MLA-11.csv) | 2 | Historical restart-scout stress summary; superseded because runs recorded 9,406–9,413 evaluations and the w/o RS arm used a trial-counter reset |
| [MLA-12.csv](2.Mechanism-level%20attribution/MLA-12.csv) | 100 | Its per-run records |
| [MLA-13.csv](2.Mechanism-level%20attribution/MLA-13.csv) | 1 | Its paired statistics |

## 3.Sensitivity analysis

| CSV | Rows | Content |
|---|---|---|
| [SA-1.csv](3.Sensitivity%20analysis/SA-1.csv) | 5 | Demand re-optimization, 30 runs per level (demand scale 0.8–1.2; Table 13) |
| [SA-2.csv](3.Sensitivity%20analysis/SA-2.csv) | 5 | Fixed-plan robustness under the same demand levels |

## 4.Forced control

| CSV | Rows | Content |
|---|---|---|
| [FC-1.csv](4.Forced%20control/FC-1.csv) | 2 | Restart-limit control transcribed from Table 14: default L_R = 30 vs forced L_R = 10 (premature restarts); per-run records for this control predate the revision chain |
