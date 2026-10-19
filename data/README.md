# Result Data (`D-1.csv` ... `D-58.csv`)

The 58 curated result tables of this repository (35 main-text + 23 supplementary), stored as UTF-8 CSV and numbered in the order their tables appear in the manuscript: main-text tables first (Tables 7-20 of the revised manuscript), then the supplementary sections (S1-S10). The historical Excel workbooks (`4-*.xlsx`, `S*.xlsx`) were replaced by these CSV files; the `Source workbook` column below retains the historical file name for provenance.

Note on robustness blocks: the current manuscript orders them as Table 16 (objective weights) - Table 17 (penalties) - Table 18 (dwell coefficients), which differs from the legacy experiment numbering (`4-8` = dwell, `4-9` = weights, `4-10` = penalties); the `D-` numbering follows the manuscript.

| CSV | Source workbook (historical) | Manuscript anchor | Data rows | Content |
|---|---|---|---|---|
| [`D-1.csv`](D-1.csv) | `4-2.xlsx` | Table 7 | 8 | Operation performance: original vs optimized metrics |
| [`D-2.csv`](D-2.csv) | `4-1.xlsx` | Table 8 | 7 | Original vs optimized departures and headways by period |
| [`D-3.csv`](D-3.csv) | `4-3.xlsx` | Table 10 | 10 | Competing-algorithm performance (S3/S4, CPU time, convergence, rank) |
| [`D-4.csv`](D-4.csv) | `4-3-2.xlsx` | Table 10 | 40 | Extended per-scenario algorithm summary (S1-S4) |
| [`D-5.csv`](D-5.csv) | `4-3-3.xlsx` | Table 10 | 400 | Per-run records of the algorithm comparison (10 runs x 10 algorithms x 4 scenarios) |
| [`D-6.csv`](D-6.csv) | `4-4.xlsx` | Table 11 | 48 | Algorithm output schemes under S1-S4 (operational metrics) |
| [`D-7.csv`](D-7.csv) | `4-4-2.xlsx` | Table 11 | 48 | Extended operational metrics under S1-S4 |
| [`D-8.csv`](D-8.csv) | `4-4-3.xlsx` | Table 11 | 320 | Per-run operational records (8 algorithms x 4 scenarios x 10 runs) |
| [`D-9.csv`](D-9.csv) | `4-5.xlsx` | Sec. 4.3.1 | 10 | Significance tests: Friedman, Wilcoxon, Holm, A12 (original comparison scope) |
| [`D-10.csv`](D-10.csv) | `4-5-2.xlsx` | Sec. 4.3.1 | 10 | Significance tests, alternate layout |
| [`D-11.csv`](D-11.csv) | `4-5-3.xlsx` | Sec. 4.3.1 | 400 | Per-run records feeding the significance tests |
| [`D-12.csv`](D-12.csv) | `4-6.xlsx` | Table 14 | 12 | Parameter sensitivity of SHDMS-ABC, one-factor grid |
| [`D-13.csv`](D-13.csv) | `4-6-2.xlsx` | Table 14 | 27 | Parameter sensitivity, extended value grid |
| [`D-14.csv`](D-14.csv) | `4-6-3.xlsx` | Table 14 | 270 | Parameter sensitivity, per-run records (270 runs) |
| [`D-15.csv`](D-15.csv) | `4-7.xlsx` | Table 15 | 6 | Ablation study, pre-revision 10-run version |
| [`D-16.csv`](D-16.csv) | `4-7-2.xlsx` | Table S5 | 6 | Ablation on New City Express |
| [`D-17.csv`](D-17.csv) | `4-7-3.xlsx` | Table S5 | 6 | Ablation on Wuxiao Intercity |
| [`D-18.csv`](D-18.csv) | `4-7-4.xlsx` | Table S5 | 6 | Ablation on Suishen Intercity |
| [`D-19.csv`](D-19.csv) | `4-7-5.xlsx` | Table S5 | 6 | Ablation on Beijing Sub-Center |
| [`D-20.csv`](D-20.csv) | `4-7-6.xlsx` | Table S5 | 300 | Ablation per-run records, five datasets (300 runs) |
| [`D-21.csv`](D-21.csv) | `4-9.xlsx` | Table 16 | 9 | Objective-weight robustness (each weight +/-25%) |
| [`D-22.csv`](D-22.csv) | `4-9-2.xlsx` | Table 16 | 9 | Objective-weight robustness, linked version |
| [`D-23.csv`](D-23.csv) | `4-9-3.xlsx` | Table 16 | 45 | Weight-robustness per-run records (45 runs) |
| [`D-24.csv`](D-24.csv) | `4-10.xlsx` | Table 17 | 11 | Penalty-parameter robustness (x0.5 / x2.0) |
| [`D-25.csv`](D-25.csv) | `4-10-2.xlsx` | Table 17 | 11 | Penalty-parameter robustness, linked version |
| [`D-26.csv`](D-26.csv) | `4-10-3.xlsx` | Table 17 | 55 | Penalty-robustness per-run records (55 runs) |
| [`D-27.csv`](D-27.csv) | `4-8.xlsx` | Table 18 | 5 | Dwell-time coefficient robustness (eta1/eta2 +/-20%) |
| [`D-28.csv`](D-28.csv) | `4-8-2.xlsx` | Table 18 | 5 | Dwell-time coefficient robustness, linked version |
| [`D-29.csv`](D-29.csv) | `4-8-3.xlsx` | Table 18 | 25 | Coefficient-robustness per-run records (25 runs) |
| [`D-30.csv`](D-30.csv) | `4-11.xlsx` | Table 20 | 5 | Cross-line operational effects, five railway lines |
| [`D-31.csv`](D-31.csv) | `4-11-2.xlsx` | Table 20 | 5 | Cross-line SHDMS-ABC baseline vs optimized |
| [`D-32.csv`](D-32.csv) | `4-11-3.xlsx` | Table 20 | 250 | Cross-line per-run records, SHDMS-ABC (50 runs x 5 lines) |
| [`D-33.csv`](D-33.csv) | `4-12.xlsx` | Table S9 | 6 | Cross-line algorithm comparison (10 algorithms x 5 lines) |
| [`D-34.csv`](D-34.csv) | `4-12-2.xlsx` | Table S9 | 50 | Cross-line algorithm comparison, extended layout |
| [`D-35.csv`](D-35.csv) | `4-12-3.xlsx` | Table S9 | 2500 | Cross-line per-run records (10 algorithms x 5 lines x 50 runs) |
| [`D-36.csv`](D-36.csv) | `supplement/S1.xlsx` | Table S1 | 40 | Multi-scenario algorithm summary (S1-S4, 10 methods) |
| [`D-37.csv`](D-37.csv) | `supplement/S2.xlsx` | Table S2 | 48 | Multi-scenario operational outcomes (S1-S4, 12 methods) |
| [`D-38.csv`](D-38.csv) | `supplement/S3.xlsx` | Table S3 | 10 | Statistical significance and effect-size analysis |
| [`D-39.csv`](D-39.csv) | `supplement/S4-1.xlsx` | Table S4 | 27 | One-factor parameter sensitivity, extended value grid |
| [`D-40.csv`](D-40.csv) | `supplement/S4-2.xlsx` | Table S4 | 18 | Two-factor parameter grid (beta/alpha/rho/LR) |
| [`D-41.csv`](D-41.csv) | `supplement/S5-1.xlsx` | Table S5 | 28 | Multi-dataset ablation: variant differences and tests |
| [`D-42.csv`](D-42.csv) | `supplement/S5-2.xlsx` | Table S5 | 24 | Multi-dataset ablation summary (best/mean/convergence/runtime) |
| [`D-43.csv`](D-43.csv) | `supplement/S6-1.xlsx` | Table S6 | 9 | Objective-weight one-factor robustness (+/-25%) |
| [`D-44.csv`](D-44.csv) | `supplement/S6-2.xlsx` | Table S6 | 25 | Single-weight scale profiles (x0.50-x1.50) |
| [`D-45.csv`](D-45.csv) | `supplement/S6-3.xlsx` | Table S6 | 150 | Weight-pair scale profiles |
| [`D-46.csv`](D-46.csv) | `supplement/S6-4.xlsx` | Table S6 | 81 | Full weight-set scale profiles |
| [`D-47.csv`](D-47.csv) | `supplement/S6-5.xlsx` | Table S6 | 8 | Preference-based weight profiles |
| [`D-48.csv`](D-48.csv) | `supplement/S7-1.xlsx` | Table S7 | 11 | Penalty one-factor robustness (x0.5 / x2.0) |
| [`D-49.csv`](D-49.csv) | `supplement/S7-2.xlsx` | Table S7 | 250 | Penalty-pair scale profiles |
| [`D-50.csv`](D-50.csv) | `supplement/S7-3.xlsx` | Table S7 | 243 | Full penalty-set scale profiles |
| [`D-51.csv`](D-51.csv) | `supplement/S8-1.xlsx` | Table S8 | 7 | eta1 sweep at fixed eta2 (response surface) |
| [`D-52.csv`](D-52.csv) | `supplement/S8-2.xlsx` | Table S8 | 7 | eta2 sweep at fixed eta1 |
| [`D-53.csv`](D-53.csv) | `supplement/S8-3.xlsx` | Table S8 | 25 | eta1-eta2 grid (5 x 5) |
| [`D-54.csv`](D-54.csv) | `supplement/S9-1.xlsx` | Table S9 | 50 | Cross-line algorithm comparison, operational metrics |
| [`D-55.csv`](D-55.csv) | `supplement/S9-2.xlsx` | Table S9 | 6 | Cross-line composite objectives and average ranks |
| [`D-56.csv`](D-56.csv) | `supplement/S10-1.xlsx` | Table S10 | 40 | Dataset field dictionary: timetable records |
| [`D-57.csv`](D-57.csv) | `supplement/S10-2.xlsx` | Table S10 | 10 | Dataset field dictionary: station-period demand |
| [`D-58.csv`](D-58.csv) | `supplement/S10-3.xlsx` | Table S10 | 7 | Dataset field dictionary: station attributes |

Revision re-run outputs (Tables 6, 12, 13, 15, 20 sources) are machine-readable JSON/CSV in [`revision/`](revision) and are not duplicated here.

**Known caveats (documented for reproducibility):**
1. `D-1.csv` (4-2.xlsx) reports the submission-version operational metrics of the 55-service plan (objective 2.9169, utilization 90.28%); the revised manuscript Table 7 uses the published 57-service plan with objective 6.8920 and utilization 93.75% - see `revision/` for the revised source.
2. `D-31.csv` (4-11-2.xlsx) NST-HSR row (1.8619 +/- 3.4068) is the submission-version 10-run statistic; the revised manuscript Table 20 NST-HSR rows follow the unified-protocol 30-run re-run (see `revision/cross_line_baseline_vs_optimized.json`).
3. The 4-5 series (D-9/D-10/D-11) and S3 (D-38) contain identical significance-test content; both are retained as found.
4. Tables 6, 9, 12, 13, 15, and 19 of the revised manuscript draw on `revision/` outputs and dataset workbooks rather than these 58 tables.
