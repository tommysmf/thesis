# Cotton candy semi-synthetic generator

A prescriptive process monitoring (PresPM) benchmark built on real IoT data: **when should spinning start
while the cotton candy machine heats up?** Every case is a real heating curve from the
[TUM cotton candy dataset](https://zenodo.org/records/17226615); the historical policy and the outcome are
specified, so the true outcome of every possible start moment is known.

Design: see the doc *Cotton candy toy setup: specification*. Results of the checks: `validation_report.md`.

## Getting the data

The raw data is not in this repository (356 MB). To rebuild it:

1. Download the dataset from Zenodo: [Cotton Candy XES YAML](https://zenodo.org/records/17226615)
   (TUM, 2025). Credit the authors and follow the license stated on that page when you reuse it.
2. Unzip it into `datasets/cotton-candy/`, so the `batch-*` folders sit directly in that folder.
3. Run `python datasets/cotton-candy/prepare_cotton_candy.py` from the thesis folder. It writes
   `datasets/cotton-candy/processed/` (`runs.csv`, `sensors.csv`, `events.csv`, about 8 MB).

Generated datasets (`cc_generator/output/`) are not committed either: the same config and seed
always give the same data, so rebuild them with `generate.py`.

## Quick start

```
pip install numpy pandas
python generate.py --processed ../datasets/cotton-candy/processed --out output/default
python validate.py --processed ../datasets/cotton-candy/processed
python tests/test_generator.py ../datasets/cotton-candy/processed
```

`--processed` is the folder written by `datasets/cotton-candy/prepare_cotton_candy.py`
(`runs.csv`, `sensors.csv`, `events.csv`). Override knobs with `--set key=value`, e.g.
`--set delta=0 --set resamples_per_curve=50`.

## What a case is

| Element | Source |
|---|---|
| Case | One candy: a real run, resampled `resamples_per_curve` times with fresh random draws |
| Decision points | Every 2 s from "stick placed" (~19 s after machine on) to the head's first temperature peak (~160 s): ~70 points |
| State at a point | Head temperature (real curve; after the real start slowed by 0.8 because spinning heats faster), its 10 s slope, ambient temperature and humidity, iterations since maintenance |
| Action | Start spinning now, or wait; the last point starts automatically |
| Historical policy | With probability `delta` a temperature rule: start chance `sigmoid(beta*(head-58) + gamma*(t-22))`, clipped to [eps, 1-eps]; otherwise a uniformly random start moment |
| Outcome (g) | `W_max*exp(-((head - h_opt)/w)^2) - lam*t + noise`, with `h_opt = h0 + a_wear*(wear-30)/30 + b_humidity*z(humidity)` |

## Outputs

```
output/<name>/
  config.json               the knobs used
  observed/                 what a method may train on
    event_log.csv           real setup events, synthetic "Start spinning", "Candy finished" (weight)
    sensor_stream.csv       sensor readings up to the start
    decision_points.csv     state per decision point up to the start + whether it started there
    cases.csv               per case: attributes, split (train/test by real curve), start moment, observed y
  truth/                    for scoring only, never for training
    answer_key.csv          per case x decision point: true start chance, outcome if started there
    case_truth.csv          per case: optimal temperature, best start moment, regret of the historical start
```

Online mode (like SimBank), for policies that act step by step:

```python
from ccgen import Config, load_curves, CottonCandyEnv
env = CottonCandyEnv(load_curves("../datasets/cotton-candy/processed"), Config(), split="test")
obs = env.reset()
while True:
    obs, reward, done, info = env.step(1 if obs["head"] >= 64 else 0)
    if done:
        break
print(reward, info["regret"])
```

## Knobs (ccgen/config.py)

| Knob | Default | Controls |
|---|---|---|
| `delta` | 0.95 | Share of cases following the historical rule (confounding, SimBank-style; 0 = randomized) |
| `beta`, `h_star`, `gamma`, `t_star` | 0.3, 58 C, 0.05, 22 s | Shape of the historical rule |
| `eps` | 0.01 | Minimum start/wait chance per point (overlap) |
| `W_max`, `h0`, `w` | 10.5 g, 64 C, 22 C | Size of the timing effect |
| `a_wear`, `b_humidity` | 8 C, -4 C | Heterogeneity of the optimal moment (how much personalization matters) |
| `lam` | 0.01 g/s | Time cost of waiting |
| `noise_sd` | 0.4 g | Case-level outcome noise |
| `after_start_slowdown` | 0.8 | Heating correction after the real start |
| `grid_seconds` | 2 s | Decision grid |
| `resamples_per_curve`, `test_share`, `seed` | 20, 0.3, 0 | Dataset size and split |

## Known limitations

- Weights spread wider than in the real data (5.2-10.2 g vs 7.1-9.7 g for the middle 80%); the real weights barely
  depend on timing, so a benchmark where timing matters cannot match them exactly. The median (8.6 g) matches.
- `beta` changes how much the rule depends on temperature, but the resulting naive bias is not monotone in it;
  use `delta` to control confounding strength.
- 177 real curves: resampling adds random draws, not new curves (`curve_stretch` adds some variety).
- Events after the start (spinning, measuring) are not simulated; the case ends with the outcome.
