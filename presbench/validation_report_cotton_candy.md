# Validation report

Adapter: `cotton_candy`. Settings: `{'core': {'delta': 0.95, 'noise_sd': 0.4, 'resamples_per_case': 20, 'test_share': 0.3, 'seed': 0}, 'adapter': {'W_max': 9.3, 'h0': 65.0, 'w': 40.0, 'w_cold': 0.0, 'w_hot': 0.0, 'a_wear': 8.0, 'b_humidity': 0.0, 'lam': 0.01, 'energy_price': 0.0, 'hidden_effect': 0.0, 'hidden_policy': 0.0, 'pool_size': 3}}`

3420 cases from 171 real cases; decision points per case (27.0, 48.0, 53.0) (p10 / median / p90).

## 1. Realism (generated vs real, p10 / median / p90)

| Quantity | Generated | Real |
|---|---|---|
| controller arm: head reading at start (C) | (54.1, 57.0, 68.2) | (53.4, 56.6, 68.0) |
| controller arm: wait after stick placed (s) | (0.2, 9.6, 42.5) | (2.6, 6.5, 38.2) |
| fixed-wait arm: wait after stick placed (s) | (25.9, 47.2, 104.9) | (24.8, 47.1, 104.5) |
| observed weight (g) | (7.6, 8.8, 9.5) | (7.1, 8.6, 9.7) |

Fixed-wait arm, correlation between head temperature at "stick placed" and waiting time: generated -0.57, real -0.64 (cold machines wait longer).

Mean weight by head reading at the start (real runs, one 17.4 g outlier excluded, vs generated
historical cases). The outcome is specified, not fitted; this is a sanity check only.

| Head at start | (0, 55] | (55, 60] | (60, 65] | (65, 70] | (70, 75] | (75, 80] | (80, 95] |
|---|---|---|---|---|---|---|---|
| Real (g) | 8.19 (n=27) | 8.80 (n=22) | 8.79 (n=17) | 8.42 (n=16) | 8.56 (n=33) | 8.49 (n=24) | 8.23 (n=8) |
| Generated (g) | 8.51 | 8.83 | 8.91 | 8.95 | 8.81 | 8.35 | 7.07 |

## 2. Baselines and confounding (defaults; mean +- sd over seeds [0, 1, 2])

| Quantity | Value |
|---|---|
| historical policy | 8.23 +- 0.02 |
| best fixed delay | 8.43 +- 0.04 |
| best threshold, current reading | 8.76 +- 0.02 |
| best threshold, 10 s mean | 8.76 +- 0.02 |
| oracle | 8.91 +- 0.01 |
| best is the first point (share) | 0.20 +- 0.04 |
| naive error | -0.49 +- 0.02 |

Naive error = (naive estimate - truth) of the effect of intervening 10-40 s instead of 0-4 s after the window opens.

## 3. Knobs

`delta`:

| delta | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 0.0 | 8.03 +- 0.04 | 8.76 +- 0.02 | 8.76 +- 0.02 | 8.91 +- 0.01 | -0.04 +- 0.10 |
| 0.5 | 8.11 +- 0.00 | 8.76 +- 0.02 | 8.76 +- 0.02 | 8.91 +- 0.01 | -0.32 +- 0.03 |
| 0.95 | 8.23 +- 0.02 | 8.76 +- 0.02 | 8.76 +- 0.02 | 8.91 +- 0.01 | -0.49 +- 0.02 |
| 1.0 | 8.24 +- 0.04 | 8.76 +- 0.02 | 8.76 +- 0.02 | 8.91 +- 0.01 | -0.51 +- 0.02 |

`w`:

| w | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 20.0 | 6.79 +- 0.05 | 8.16 +- 0.03 | 8.16 +- 0.03 | 8.72 +- 0.02 | -1.22 +- 0.04 |
| 30.0 | 7.79 +- 0.04 | 8.58 +- 0.03 | 8.57 +- 0.03 | 8.84 +- 0.01 | -0.75 +- 0.02 |
| 40.0 | 8.23 +- 0.02 | 8.76 +- 0.02 | 8.76 +- 0.02 | 8.91 +- 0.01 | -0.49 +- 0.02 |
| 60.0 | 8.58 +- 0.01 | 8.94 +- 0.02 | 8.94 +- 0.02 | 8.99 +- 0.01 | -0.25 +- 0.02 |

`h0`:

| h0 | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 60.0 | 8.10 +- 0.02 | 8.89 +- 0.02 | 8.89 +- 0.02 | 8.98 +- 0.01 | -0.61 +- 0.01 |
| 65.0 | 8.23 +- 0.02 | 8.76 +- 0.02 | 8.76 +- 0.02 | 8.91 +- 0.01 | -0.49 +- 0.02 |
| 70.0 | 8.14 +- 0.07 | 8.59 +- 0.02 | 8.57 +- 0.03 | 8.75 +- 0.02 | -0.33 +- 0.03 |

`a_wear`:

| a_wear | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 0.0 | 8.37 +- 0.02 | 8.92 +- 0.01 | 8.91 +- 0.01 | 8.93 +- 0.01 | -0.37 +- 0.02 |
| 8.0 | 8.23 +- 0.02 | 8.76 +- 0.02 | 8.76 +- 0.02 | 8.91 +- 0.01 | -0.49 +- 0.02 |
| 16.0 | 7.82 +- 0.06 | 8.31 +- 0.03 | 8.31 +- 0.03 | 8.77 +- 0.01 | -0.64 +- 0.02 |

## 4. Scenarios

| scenario | historical | best threshold, current reading | best threshold, 10 s mean | observable oracle | oracle | naive error |
|---|---|---|---|---|---|---|
| realistic | 8.23 +- 0.02 | 8.76 +- 0.02 | 8.76 +- 0.02 | 8.91 +- 0.01 | 8.91 +- 0.01 | -0.49 +- 0.02 |
| hidden-confounding | 8.17 +- 0.03 | 8.64 +- 0.02 | 8.63 +- 0.02 | 8.77 +- 0.01 | 8.86 +- 0.02 | -0.74 +- 0.05 |
| asymmetric | 6.84 +- 0.20 | 8.16 +- 0.05 | 8.16 +- 0.04 | 8.74 +- 0.01 | 8.74 +- 0.01 | -0.78 +- 0.07 |
| energy | 8.24 +- 0.03 | 8.76 +- 0.02 | 8.76 +- 0.03 | 8.91 +- 0.01 | 8.91 +- 0.01 | -0.49 +- 0.02 |
