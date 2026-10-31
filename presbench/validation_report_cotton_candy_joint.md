# Validation report (two linked decisions)

Adapter: `cotton_candy_joint` (start, then stop). Settings: `{'core': {'delta': 0.95, 'noise_sd': 0.8, 'resamples_per_case': 5, 'test_share': 0.3, 'seed': 0}, 'adapter': {'h0': 65.0, 'w': 40.0, 'a_wear': 8.0, 'W_max': 9.3, 'tau': 5.0, 'T_cold': 70.0, 'cold_slope': 0.45, 'energy_price': 0.037, 'stress_price': 0.01, 'T_stress': 85.0, 'lam': 0.0, 'hidden_effect': 0.0, 'hidden_policy': 0.0, 'pool_size': 3}}`

855 cases from 171 real cases; (start, stop) paths per case (728.0, 2434.0, 3564.0) (p10 / median / p90).

## 1. Realism (generated historical cases vs real, p10 / median / p90)

| Quantity | Generated | Real |
|---|---|---|
| wait after stick placed (s) | (3.9, 33.2, 90.9) | (2.8, 32.6, 94.5) |
| spin duration (s) | (52.6, 74.7, 93.0) | (51.0, 73.4, 89.8) |
| head at start (C) | (54.3, 67.0, 77.3) | (54.1, 67.3, 77.9) |
| head at stop (C) | (69.4, 78.7, 93.8) | (67.7, 77.7, 93.0) |
| observed weight (g) | (6.8, 8.5, 9.8) | (7.1, 8.6, 9.7) |

How the decisions interact: the best spin length after each possible start, by the head temperature at that start (one resample per run; Spearman -0.89).

| Head at start (C) | (0, 55] | (55, 60] | (60, 65] | (65, 70] | (70, 75] | (75, 80] | (80, 100] |
|---|---|---|---|---|---|---|---|
| Best spin (s, median) | 77 | 54 | 34 | 26 | 26 | 26 | 21 |

## 2. Policies (test cases, expected KPI; mean +- sd over seeds [0, 1, 2])

| Policy | Value |
|---|---|
| historical | 7.25 +- 0.07 |
| best second after historical first | 7.77 +- 0.01 |
| greedy | 8.43 +- 0.02 |
| best fixed delays | 7.31 +- 0.06 |
| best thresholds | 8.33 +- 0.01 |
| observable oracle | 8.48 +- 0.01 |
| oracle | 8.48 +- 0.01 |
| naive error (second stage) | -0.40 +- 0.02 |

Best fixed delays (seed 0): wait 40 s, then stop after 75 s. Best thresholds: start at 64.0, stop at 71.4 after at least 20 s.

Greedy = the start chosen as if the historical policy then decides the stop, followed by the best stop. Greedy vs oracle = what deciding both together is worth.

Naive error = (naive estimate - truth) of the effect of a 70-95 s instead of a 40-60 s phase between the two decisions, at the historical start.

## 3. Knobs

`delta`:

| delta | historical | greedy | best thresholds | oracle | naive error (second stage) |
|---|---|---|---|---|---|
| 0.0 | 6.45 +- 0.13 | 8.39 +- 0.02 | 8.33 +- 0.01 | 8.48 +- 0.01 | 0.12 +- 0.15 |
| 0.5 | 6.77 +- 0.03 | 8.44 +- 0.02 | 8.33 +- 0.01 | 8.48 +- 0.01 | -0.16 +- 0.15 |
| 0.95 | 7.25 +- 0.07 | 8.43 +- 0.02 | 8.33 +- 0.01 | 8.48 +- 0.01 | -0.40 +- 0.02 |
| 1.0 | 7.28 +- 0.08 | 8.43 +- 0.02 | 8.33 +- 0.01 | 8.48 +- 0.01 | -0.42 +- 0.04 |

`cold_slope`:

| cold_slope | historical | greedy | best thresholds | oracle | naive error (second stage) |
|---|---|---|---|---|---|
| 0.0 | 7.40 +- 0.02 | 8.58 +- 0.02 | 8.42 +- 0.03 | 8.59 +- 0.02 | -0.12 +- 0.06 |
| 0.2 | 7.33 +- 0.04 | 8.45 +- 0.01 | 8.34 +- 0.02 | 8.49 +- 0.01 | -0.25 +- 0.04 |
| 0.45 | 7.25 +- 0.07 | 8.43 +- 0.02 | 8.33 +- 0.01 | 8.48 +- 0.01 | -0.40 +- 0.02 |
| 0.7 | 7.18 +- 0.10 | 8.42 +- 0.03 | 8.32 +- 0.01 | 8.48 +- 0.01 | -0.56 +- 0.04 |

`w`:

| w | historical | greedy | best thresholds | oracle | naive error (second stage) |
|---|---|---|---|---|---|
| 20.0 | 5.81 +- 0.03 | 8.28 +- 0.03 | 7.76 +- 0.03 | 8.30 +- 0.03 | -0.48 +- 0.05 |
| 40.0 | 7.25 +- 0.07 | 8.43 +- 0.02 | 8.33 +- 0.01 | 8.48 +- 0.01 | -0.40 +- 0.02 |
| 60.0 | 7.60 +- 0.09 | 8.49 +- 0.01 | 8.45 +- 0.01 | 8.55 +- 0.01 | -0.38 +- 0.02 |

`T_cold`:

| T_cold | historical | greedy | best thresholds | oracle | naive error (second stage) |
|---|---|---|---|---|---|
| 65.0 | 7.35 +- 0.04 | 8.55 +- 0.01 | 8.41 +- 0.03 | 8.57 +- 0.01 | -0.13 +- 0.06 |
| 70.0 | 7.25 +- 0.07 | 8.43 +- 0.02 | 8.33 +- 0.01 | 8.48 +- 0.01 | -0.40 +- 0.02 |
| 75.0 | 6.69 +- 0.02 | 8.22 +- 0.06 | 8.08 +- 0.06 | 8.30 +- 0.04 | -0.96 +- 0.06 |

`energy_price`:

| energy_price | historical | greedy | best thresholds | oracle | naive error (second stage) |
|---|---|---|---|---|---|
| 0.0 | 8.39 +- 0.07 | 9.21 +- 0.03 | 9.09 +- 0.02 | 9.24 +- 0.02 | -0.37 +- 0.01 |
| 0.037 | 7.25 +- 0.07 | 8.43 +- 0.02 | 8.33 +- 0.01 | 8.48 +- 0.01 | -0.40 +- 0.02 |
| 0.1 | 5.31 +- 0.09 | 7.21 +- 0.05 | 7.18 +- 0.06 | 7.38 +- 0.03 | -0.46 +- 0.04 |
| 0.2 | 2.24 +- 0.11 | 5.48 +- 0.14 | 5.45 +- 0.13 | 5.79 +- 0.13 | -0.55 +- 0.07 |

## 4. Scenarios

| scenario | historical | greedy | best thresholds | observable oracle | oracle | naive error (second stage) |
|---|---|---|---|---|---|---|
| realistic | 7.25 +- 0.07 | 8.43 +- 0.02 | 8.33 +- 0.01 | 8.48 +- 0.01 | 8.48 +- 0.01 | -0.40 +- 0.02 |
| no-cold-effect | 7.40 +- 0.02 | 8.58 +- 0.02 | 8.42 +- 0.03 | 8.59 +- 0.02 | 8.59 +- 0.02 | -0.12 +- 0.06 |
| hidden-confounding | 7.16 +- 0.07 | 8.36 +- 0.01 | 8.18 +- 0.03 | 8.34 +- 0.02 | 8.42 +- 0.01 | -0.41 +- 0.05 |
| costly-time | 2.24 +- 0.11 | 5.48 +- 0.14 | 5.45 +- 0.13 | 5.79 +- 0.13 | 5.79 +- 0.13 | -0.55 +- 0.07 |
