# Validation report

Config: `{'grid_seconds': 2.0, 'after_start_slowdown': 0.8, 'curve_stretch': 0.0, 'beta': 0.3, 'h_star': 58.0, 'gamma': 0.05, 't_star': 22.0, 'eps': 0.01, 'delta': 0.95, 'W_max': 10.5, 'h0': 64.0, 'w': 22.0, 'a_wear': 8.0, 'b_humidity': -4.0, 'lam': 0.01, 'noise_sd': 0.4, 'resamples_per_curve': 20, 'test_share': 0.3, 'seed': 0}`

## 1. Realism (generated vs real, p10 / median / p90)

| Quantity | Generated | Real |
|---|---|---|
| start time (s after machine on) | (16.6, 21.1, 53.1) | (19.0, 22.3, 38.9) |
| start head temperature (C) | (52.1, 57.7, 70.3) | (50.7, 58.1, 70.0) |
| observed outcome (g) | (5.2, 8.5, 10.2) | (7.1, 8.6, 9.7) |

## 2. Confounding: waiting 10-40 s vs starting right away

True effect +0.43 g; naive comparison of observed cases -0.80 g (2370 early starters vs 438 late starters).

## 3. Baseline policies (test curves, expected outcome in g)

| Policy | Value |
|---|---|
| start at ready | 7.58 |
| historical policy | 7.91 |
| best fixed delay (30 s after ready) | 8.37 |
| best fixed threshold (start at 64 C) | 9.23 |
| oracle (best moment per case) | 9.69 |

## 4. Knobs

Confounding share delta (SimBank-style; true vs naive effect of waiting 10-40 s):

| delta | true | naive | naive error | late starters |
|---|---|---|---|---|
| 0.0 | +0.43 | +0.47 | +0.05 | 1543 |
| 0.5 | +0.43 | -0.40 | -0.82 | 1142 |
| 0.75 | +0.43 | -0.78 | -1.20 | 988 |
| 0.95 | +0.43 | -1.00 | -1.42 | 943 |
| 1.0 | +0.43 | -0.98 | -1.40 | 858 |

Temperature dependence beta of the rule (not monotone in the naive error; see README):

| beta | true | naive | naive error | late starters |
|---|---|---|---|---|
| 0.0 | +0.43 | +0.25 | -0.18 | 302 |
| 0.15 | +0.43 | -2.12 | -2.55 | 776 |
| 0.3 | +0.43 | -1.00 | -1.42 | 943 |
| 0.6 | +0.43 | -0.68 | -1.11 | 1552 |

Heterogeneity of the optimal temperature (a_wear, b_humidity scaled together):

| scale | historical | best fixed threshold | oracle | oracle - threshold |
|---|---|---|---|---|
| 0.0 | 8.72 | 9.83 | 9.84 | 0.01 |
| 0.5 | 8.39 | 9.65 | 9.79 | 0.14 |
| 1.0 | 7.90 | 9.23 | 9.69 | 0.46 |
| 1.5 | 7.36 | 8.63 | 9.52 | 0.89 |

Heating correction after the real start (sensitivity of the conclusions):

| slowdown | historical | oracle | gap |
|---|---|---|---|
| 0.7 | 7.91 | 9.62 | 1.71 |
| 0.8 | 7.90 | 9.69 | 1.79 |
| 0.9 | 7.90 | 9.74 | 1.84 |
| 1.0 | 7.89 | 9.78 | 1.89 |
