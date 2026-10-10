# Validation report

Config: `{'delta': 0.95, 'W_max': 9.3, 'h0': 65.0, 'w': 40.0, 'w_cold': 0.0, 'w_hot': 0.0, 'a_wear': 8.0, 'b_humidity': 0.0, 'lam': 0.01, 'noise_sd': 0.4, 'hidden_effect': 0.0, 'hidden_policy': 0.0, 'pool_size': 3, 'resamples_per_curve': 20, 'test_share': 0.3, 'seed': 0}`

3420 cases from 171 real curves (69 from controller batches); decision points per case (27.0, 48.0, 53.0) (p10 / median / p90).

## 1. Realism (generated vs real, p10 / median / p90)

| Quantity | Generated | Real |
|---|---|---|
| controller arm: head reading at start (C) | (54.1, 57.0, 68.0) | (53.4, 56.6, 68.0) |
| controller arm: wait after stick placed (s) | (0.1, 8.5, 40.1) | (2.6, 6.5, 38.2) |
| fixed-wait arm: wait after stick placed (s) | (24.0, 47.3, 105.0) | (24.8, 47.1, 104.5) |
| observed weight (g) | (7.6, 8.7, 9.5) | (7.1, 8.6, 9.7) |

Fixed-wait arm, correlation between head temperature at "stick placed" and waiting time: generated -0.57, real -0.64 (cold machines wait longer).

Mean weight by head reading at the start (real runs vs generated historical cases). The outcome is
specified, not fitted; the real comparison is small, confounded and almost flat (one 17.4 g outlier
excluded), so it is a sanity check only.

| Head at start | (0, 55] | (55, 60] | (60, 65] | (65, 70] | (70, 75] | (75, 80] | (80, 95] |
|---|---|---|---|---|---|---|---|
| Real (g) | 8.19 (n=27) | 8.80 (n=22) | 8.79 (n=17) | 8.42 (n=16) | 8.56 (n=33) | 8.49 (n=24) | 8.23 (n=8) |
| Generated (g) | 8.53 | 8.82 | 8.87 | 8.97 | 8.83 | 8.33 | 7.08 |

## 2. Baselines and confounding (realistic defaults; mean +- sd over seeds [0, 1, 2])

| Quantity | Value |
|---|---|
| historical policy | 8.23 +- 0.03 |
| best fixed delay | 8.43 +- 0.04 |
| best threshold, current reading | 8.76 +- 0.02 |
| best threshold, 10 s mean | 8.75 +- 0.02 |
| oracle | 8.91 +- 0.01 |
| best is the first moment (share) | 0.20 +- 0.04 |
| naive error | -0.52 +- 0.01 |

Naive error = (naive estimate - truth) of the effect of waiting 10-40 s instead of 0-4 s.

## 3. Knobs

Share following the real batch policy, delta (the rest starts at a random moment):

| delta | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 0.0 | 8.04 +- 0.05 | 8.76 +- 0.02 | 8.75 +- 0.02 | 8.91 +- 0.01 | -0.01 +- 0.11 |
| 0.5 | 8.13 +- 0.01 | 8.76 +- 0.02 | 8.75 +- 0.02 | 8.91 +- 0.01 | -0.33 +- 0.04 |
| 0.95 | 8.23 +- 0.03 | 8.76 +- 0.02 | 8.75 +- 0.02 | 8.91 +- 0.01 | -0.52 +- 0.01 |
| 1.0 | 8.24 +- 0.04 | 8.76 +- 0.02 | 8.75 +- 0.02 | 8.91 +- 0.01 | -0.52 +- 0.00 |

Width of the outcome window w (C); W_max fixed:

| w | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 20.0 | 6.79 +- 0.07 | 8.15 +- 0.04 | 8.16 +- 0.04 | 8.72 +- 0.02 | -1.31 +- 0.01 |
| 30.0 | 7.80 +- 0.05 | 8.57 +- 0.03 | 8.58 +- 0.03 | 8.84 +- 0.01 | -0.80 +- 0.01 |
| 40.0 | 8.23 +- 0.03 | 8.76 +- 0.02 | 8.75 +- 0.02 | 8.91 +- 0.01 | -0.52 +- 0.01 |
| 60.0 | 8.58 +- 0.02 | 8.94 +- 0.02 | 8.94 +- 0.02 | 8.99 +- 0.01 | -0.27 +- 0.02 |

Optimal head temperature h0 (C):

| h0 | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 60.0 | 8.10 +- 0.01 | 8.89 +- 0.02 | 8.89 +- 0.02 | 8.98 +- 0.01 | -0.63 +- 0.01 |
| 65.0 | 8.23 +- 0.03 | 8.76 +- 0.02 | 8.75 +- 0.02 | 8.91 +- 0.01 | -0.52 +- 0.01 |
| 70.0 | 8.14 +- 0.07 | 8.59 +- 0.03 | 8.57 +- 0.02 | 8.75 +- 0.02 | -0.37 +- 0.02 |

Wear effect on the optimum a_wear (C per 30 candies):

| a_wear | historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |
|---|---|---|---|---|---|
| 0.0 | 8.37 +- 0.01 | 8.92 +- 0.01 | 8.91 +- 0.01 | 8.93 +- 0.01 | -0.38 +- 0.01 |
| 8.0 | 8.23 +- 0.03 | 8.76 +- 0.02 | 8.75 +- 0.02 | 8.91 +- 0.01 | -0.52 +- 0.01 |
| 16.0 | 7.82 +- 0.07 | 8.31 +- 0.03 | 8.30 +- 0.03 | 8.77 +- 0.01 | -0.70 +- 0.02 |

## 4. Scenarios (generate.py --scenario NAME)

| scenario | historical | best threshold, current reading | best threshold, 10 s mean | observable oracle | oracle | naive error |
|---|---|---|---|---|---|---|
| realistic | 8.23 +- 0.03 | 8.76 +- 0.02 | 8.75 +- 0.02 | 8.91 +- 0.01 | 8.91 +- 0.01 | -0.52 +- 0.01 |
| hidden-confounding | 8.17 +- 0.01 | 8.64 +- 0.02 | 8.63 +- 0.02 | 8.77 +- 0.02 | 8.86 +- 0.02 | -0.73 +- 0.05 |
| asymmetric | 6.84 +- 0.21 | 8.17 +- 0.05 | 8.14 +- 0.06 | 8.74 +- 0.01 | 8.74 +- 0.01 | -0.90 +- 0.03 |
