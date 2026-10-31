# Validation report

Adapter: `cotton_candy_stop`. Settings: `{'core': {'delta': 0.95, 'noise_sd': 0.8, 'resamples_per_case': 20, 'test_share': 0.3, 'seed': 0}, 'adapter': {'W_max': 8.9, 'tau': 5.0, 'T_cold': 70.0, 'cold_slope': 0.45, 'energy_price': 0.037, 'stress_price': 0.01, 'T_stress': 85.0, 'lam': 0.0, 'hidden_effect': 0.0, 'pool_size': 3}}`

3340 cases from 167 real cases; decision points per case (19.0, 38.0, 52.0) (p10 / median / p90).

## 1. Realism (generated vs real, p10 / median / p90)

| Quantity | Generated | Real |
|---|---|---|
| timer arm: spin duration (s) | (52.2, 72.0, 87.6) | (53.5, 73.6, 90.0) |
| timer arm: head at the stop (C) | (68.0, 78.1, 92.8) | (68.1, 77.8, 93.1) |
| observed weight (g) | (7.4, 8.7, 9.8) | (7.2, 8.6, 9.7) |

Timer arm: share of historical stops at the last decision point (the real stop): 0.88. The window ends at the real stop, so a setting longer than the run's own spin stops there.

Weight minus its batch mean, by head reading at the stop (real runs vs generated historical cases).
The cold penalty is fitted on the real runs, so these should agree roughly.

| Head at stop | (0, 65] | (65, 70] | (70, 75] | (75, 80] | (80, 85] | (85, 105] |
|---|---|---|---|---|---|---|
| Real (g) | -2.71 (n=2) | -0.10 (n=34) | +0.17 (n=24) | +0.06 (n=31) | +0.20 (n=9) | +0.02 (n=45) |
| Generated (g) | -1.63 | -0.13 | +0.25 | +0.12 | -0.03 | +0.01 |

## 2. Baselines and confounding (defaults; mean +- sd over seeds [0, 1, 2])

| Quantity | Value |
|---|---|
| historical policy | 7.81 +- 0.05 |
| best fixed delay | 7.94 +- 0.09 |
| best threshold, current reading | 8.01 +- 0.09 |
| best threshold, 10 s mean | 8.00 +- 0.10 |
| oracle | 8.38 +- 0.06 |
| best is the first point (share) | 0.00 +- 0.00 |
| naive error | -0.75 +- 0.03 |

Naive error = (naive estimate - truth) of the effect of intervening 65-90 s instead of 35-55 s after the window opens.

## 3. Knobs

`delta`:

| delta | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 0.0 | 6.80 +- 0.26 | 8.01 +- 0.09 | 8.00 +- 0.10 | 8.38 +- 0.06 | 0.02 +- 0.09 |
| 0.5 | 7.35 +- 0.13 | 8.01 +- 0.09 | 8.00 +- 0.10 | 8.38 +- 0.06 | -0.33 +- 0.08 |
| 0.95 | 7.81 +- 0.05 | 8.01 +- 0.09 | 8.00 +- 0.10 | 8.38 +- 0.06 | -0.75 +- 0.03 |
| 1.0 | 7.86 +- 0.06 | 8.01 +- 0.09 | 8.00 +- 0.10 | 8.38 +- 0.06 | -0.81 +- 0.04 |

`cold_slope`:

| cold_slope | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 0.0 | 8.12 +- 0.01 | 8.28 +- 0.03 | 8.28 +- 0.03 | 8.59 +- 0.00 | -0.05 +- 0.03 |
| 0.2 | 7.98 +- 0.02 | 8.16 +- 0.06 | 8.15 +- 0.06 | 8.45 +- 0.04 | -0.36 +- 0.03 |
| 0.45 | 7.81 +- 0.05 | 8.01 +- 0.09 | 8.00 +- 0.10 | 8.38 +- 0.06 | -0.75 +- 0.03 |
| 0.7 | 7.64 +- 0.08 | 7.85 +- 0.13 | 7.85 +- 0.13 | 8.31 +- 0.09 | -1.13 +- 0.04 |

`T_cold`:

| T_cold | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 65.0 | 8.09 +- 0.01 | 8.27 +- 0.04 | 8.27 +- 0.04 | 8.56 +- 0.01 | -0.16 +- 0.03 |
| 70.0 | 7.81 +- 0.05 | 8.01 +- 0.09 | 8.00 +- 0.10 | 8.38 +- 0.06 | -0.75 +- 0.03 |
| 75.0 | 7.01 +- 0.15 | 7.21 +- 0.18 | 7.20 +- 0.18 | 7.82 +- 0.19 | -1.63 +- 0.04 |

`stress_price`:

| stress_price | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 0.0 | 7.91 +- 0.06 | 8.02 +- 0.09 | 8.02 +- 0.09 | 8.39 +- 0.06 | -0.72 +- 0.04 |
| 0.01 | 7.81 +- 0.05 | 8.01 +- 0.09 | 8.00 +- 0.10 | 8.38 +- 0.06 | -0.75 +- 0.03 |
| 0.03 | 7.63 +- 0.03 | 7.99 +- 0.10 | 7.97 +- 0.11 | 8.37 +- 0.06 | -0.82 +- 0.03 |

## 4. Scenarios

| scenario | historical | best threshold, current reading | best threshold, 10 s mean | observable oracle | oracle | naive error |
|---|---|---|---|---|---|---|
| realistic | 7.81 +- 0.05 | 8.01 +- 0.09 | 8.00 +- 0.10 | 8.38 +- 0.06 | 8.38 +- 0.06 | -0.75 +- 0.03 |
| no-cold-effect | 8.12 +- 0.01 | 8.28 +- 0.03 | 8.28 +- 0.03 | 8.59 +- 0.00 | 8.59 +- 0.00 | -0.05 +- 0.03 |
| no-stress | 7.91 +- 0.06 | 8.02 +- 0.09 | 8.02 +- 0.09 | 8.39 +- 0.06 | 8.39 +- 0.06 | -0.72 +- 0.04 |
| hidden-confounding | 7.56 +- 0.05 | 7.75 +- 0.09 | 7.74 +- 0.10 | 8.12 +- 0.10 | 8.20 +- 0.09 | -0.92 +- 0.06 |
