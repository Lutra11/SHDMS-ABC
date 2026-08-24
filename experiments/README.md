# Experiment Code Mapping

| Experiment Entry | Description |
|---|---|
| `4-1_period_capacity_change.py` | Comparison of time-period passenger demand, train frequency, and departure intervals before and after optimization. |
| `4-2_operational_economic_comparison.py` | Comparison of operational, economic, service-quality, and constraint-related indicators before and after optimization. |
| `4-3_multiscenario_performance.py` | Performance comparison of benchmark algorithms under scenarios S3 and S4. |
| `4-4_multiscenario_operational_metrics.py` | Representative feasible operating plans and operational indicators under scenarios S1–S4. |
| `4-5_significance_tests.py` | Friedman mean-rank analysis, paired Wilcoxon signed-rank tests, Holm correction, and A12 effect-size analysis. |
| `4-6_parameter_sensitivity.py` | One-factor sensitivity analysis of the key SHDMS-ABC parameters. |
| `4-7_ablation_study.py` | Ablation study of operator weighting, success-history learning, diversity-threshold control, and restart strategy. |
| `4-8_objective_weight_robustness.py` | Robustness analysis of the four objective weights under ±25% perturbations. |
| `4-9_penalty_robustness.py` | Robustness analysis of the five constraint penalty coefficients under ×0.5 and ×2.0 perturbations. |
| `4-10_crossline_operational_effects.py` | Cross-line operational performance and computational efficiency of SHDMS-ABC on five railway datasets. |
| `4-11_crossline_algorithm_comparison.py` | Cross-line comparison of objective values and average ranks for all benchmark algorithms. |

# Unified Experimental Parameters

| Parameter | Symbol | Setting |
|---|---|---:|
| Independent runs for the main experiments | `N_run` | 10 |
| Independent runs for robustness experiments | `N_run,robustness` | 5 |
| Independent runs for cross-line experiments | `N_run,cross-line` | 50 |
| Initial population size | `SN` | 30 |
| Target number of objective-function evaluations | `NFE_target` | 6000 |
| Initialization method | — | Uniform random initialization within the decision space |
| Objective weights | `(ω1, ω2, ω3, ω4)` | `(0.35, 0.35, 0.15, 0.15)` |
| Penalty coefficients | `(λ1, λ2, λ3, λ4, λ5)` | `(2500, 300, 1200, 1800, 5000)` |
| Success-history update rate | `ρH` | 0.30 |
| Historical-credit influence strength | `α` | 1.35 |
| State-matching influence strength | `βw` | 1.05 |
| Population-diversity thresholds | `(τD,low, τD,high)` | `(0.08, 0.22)` |
| Restart trigger threshold | `LR` | 30 |
| Minimum fallback credit | `hmin` | 0.05 |
| Numerical smoothing/improvement tolerance | `ε` | `1 × 10^-12` |
