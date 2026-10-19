# Manuscript-Revision Re-run Package

Machine-readable outputs of the unified-protocol re-runs added during the manuscript revision. All re-runs use the matched evaluation protocol — population 24, cycle budget 120, abandonment limit 40 (≈6,600 evaluations per SHDMS-ABC run) — on the same NST-HSR demand and constraint model as the repository entry points, executed from the authors' research workspace with the identical SHDMS-ABC implementation and competitor algorithms.

| File | Experiment | Protocol |
|---|---|---|
| `fair_algorithm_comparison.json` / `fair_algorithm_comparison.csv` | Unified-protocol fair comparison, 9 algorithms × S1–S4 | 30 runs per algorithm per scenario, seeds 2020–2049 |
| `ablation_rerun_statistics.json` | Ablation re-run: complete vs. w/o success-history, w/o state-aware scheduling, w/o directed scout | 50 runs per variant, seeds 5000–5049 |
| `demand_sensitivity.json` / `demand_sensitivity.csv` | Demand sensitivity: re-optimized plans vs. frozen-plan robustness at δ ∈ {0.8, 0.9, 1.0, 1.1, 1.2} | 30 runs per level, seeds 2020–2049 |
| `cross_line_baseline_vs_optimized.json` | Cross-line baseline vs. optimized on the four supplementary lines | 30 runs |
| `constraint_violation_audit.json` | Constraint-violation audit: original timetable vs. optimized plan vs. manuscript reference plan | best of 30 runs |
| `passenger_perspective_comparison.json` | Passenger-perspective comparison: original timetable vs. optimized plan | best of 30 runs |

## Headline findings (computed from the files in this directory)

- **Fair comparison**: SHDMS-ABC attains the best mean score with the smallest standard deviation in every scenario — S1 `1.0353 ± 0.1624`, S2 `9.3686 ± 0.0373`, S3 `77.3033 ± 0.0283`, S4 `130.9770 ± 0.0568`.
- **Ablation**: the directed-scout restart never triggers within the budget (0 restarts in 50 runs); w/o success-history `d = −0.32` (`p = 0.065`), w/o state-aware scheduling `d = −0.02` (`p = 0.811`).
- **Demand sensitivity**: 100% demand coverage is retained through δ = 1.0, with 99.9% at δ = 1.1 and 98.3% at δ = 1.2 under re-optimization.
- **Cross-line**: supplementary-line objectives stay within 1.2% of the baseline reference (0.02%–1.11%) at the unchanged 32-train service scale.
- **Constraint audit**: the optimized plan reports zero violations in all five constraint families (residual load violation 1.44 × 10⁻⁴) versus the original timetable's demand deficit 0.0217 and load violation 0.0748; maximum capacity utilization rises from 83.33% to 93.75%.
- **Passenger perspective**: waiting time −1.91%, demand coverage 97.06% → 100%, revenue +3.03%, operating cost unchanged.
