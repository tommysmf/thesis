# Cotton candy semi-synthetic generator

A prescriptive process monitoring (PresPM) benchmark built on real IoT data: **when should spinning start
while the cotton candy machine heats up?** Every case is a real heating curve from the
[TUM cotton candy dataset](https://zenodo.org/records/17226615), the historical policy is modelled on what the
real operators did, and the outcome is specified, so the true outcome of every possible start moment is known.

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
python demo.py --processed ../datasets/cotton-candy/processed
python tests/test_generator.py ../datasets/cotton-candy/processed
```

Pick a difficulty with `--scenario` and override single knobs with `--set key=value`:

| Scenario | What it switches on |
|---|---|
| `realistic` (default) | The real curves, the real batch policies, a specified outcome; nothing else |
| `hidden-confounding` | An unobserved factor shifts both the optimum and the controller's threshold |
| `asymmetric` | Starting cold hurts more than starting hot: an outcome shape a quadratic cannot fit |

## What a case is

| Element | Source |
|---|---|
| Case | One candy: a real run, resampled `resamples_per_curve` times. Resamples share the curve, wear and humidity and differ only in the policy draw and the noise; use `--set resamples_per_curve=1` for one case per real run |
| Decision points | Every real head reading from "stick placed" to the hottest point within 120 s, never after the real spinning ended. The reading interval differs per batch (1.3, 2.3, 4.3 or 6.5 s). Decisions happen at sensor readings between process events: after "stick placed" the log has no event until the start |
| State a method sees | The event history, the head readings so far, the batch, ambient temperature and humidity, iterations since maintenance |
| Action | Start spinning now, or wait; the last point starts automatically (a candy is always made) |
| Historical policy | With probability `delta` the real operators' rule: a fixed waiting time (batches 0-14) or a temperature controller (batches 15-23), with the setting drawn from the 3 most comparable real runs (same batch, same cold/warm machine, nearest in wear; a cold machine waited about 105 s). Otherwise a uniformly random start moment (SimBank-style randomized share) |
| Outcome | Weight `W_max*exp(-((head - h_opt)/w)^2) + noise`, with `head` the reading at the start and `h_opt = h0 + a_wear*(wear-30)/30`. KPI `y` = weight minus `lam` per second waited after "stick placed" |

How the real process starts spinning (checked on the data): in batches 0-14 "Create Cotton Candy" first waits
the configured waiting time and then spins; in batches 15-23 the waiting time is ignored, a warm-up loop waits
for the head to be warm before "Create Cotton Candy" (skipped when it already is), and spinning starts right away.

## Outputs

```
output/<name>/
  config.json               the knobs used
  observed/                 what a method may train on
    event_log.csv           real setup events, synthetic "Start spinning", "Candy finished" (weight)
    sensor_stream.csv       observed head readings (real, irregular times) up to the start
    decision_points.csv     convenience view: one row per reading after "stick placed", up to the start
    cases.csv               per case: attributes, split (train/test by real curve), start moment, weight, KPI y
  truth/                    for scoring only, never for training
    answer_key.csv          per case x decision point: observed/true head, propensity given observables, outcome if started there
    case_truth.csv          per case: policy arm and setting, optimal temperature, best moment, regret, best moment from observables only
```

Online mode (like SimBank), for policies that act step by step:

```python
from ccgen import Config, load_curves, CottonCandyEnv
env = CottonCandyEnv(load_curves("../datasets/cotton-candy/processed"), Config(), split="test")
obs = env.reset()
while True:
    obs, reward, done, info = env.step(1 if obs["head"] >= 65 else 0)
    if done:
        break
print(reward, info["regret"])
```

## Knobs (ccgen/config.py)

| Knob | Default | Controls | Basis |
|---|---|---|---|
| `delta` | 0.95 | Share following the real batch policy; the rest starts at a random moment | SimBank convention |
| `h0` | 65 C | Optimal head temperature, average case | Specified (the real weights are almost flat) |
| `w`, `W_max` | 40 C, 9.3 g | Width and height of the outcome curve | Wide because the real weights barely depend on temperature; W_max sets the median weight to the real 8.6 g |
| `a_wear` | 8 C | Worn machines need a hotter head (per 30 candies) | Specified, not measured |
| `b_humidity` | 0 | Humidity shift of the optimum | Off: no support in the data |
| `lam` | 0.01 g/s | Time cost in the KPI (not a loss of candy) | Specified; ask the supervisor |
| `noise_sd` | 0.4 g | Case-level noise on the weight | Specified |
| `w_cold`, `w_hot` | off | Asymmetric window | Scenario only |
| `hidden_effect`, `hidden_policy` | off | Hidden confounding | Scenario only |
| `pool_size` | 3 | Comparable real runs a policy setting is drawn from | Specified |
| `resamples_per_curve`, `test_share`, `seed` | 20, 0.3, 0 | Dataset size and split | |

## Known limitations

- The outcome is specified, not fitted: the real weights barely depend on the start temperature (8.2-8.8 g in
  every 5 C band once one 17.4 g outlier is removed).
- **Heating after the real spin start is replayed as if still waiting**, but the data show spinning slows it:
  at 65-75 C the head heats 0.27 C/s before the real start and 0.17 C/s after it. About two thirds of the
  decision points come from that part of the curve, so a waiting head rises too slowly there. A fitted heating
  model per run would fix this; it is an open decision.
- At the defaults a correctly shaped regression on the current reading gets most of the possible gain; the
  scenarios make the benchmark harder.
- 171 real curves (about 120 for training). With resamples, a method sees the same candy started at several
  moments, which real data never allow; `resamples_per_curve=1` avoids that at the cost of a tiny dataset.
- Decisions are possible at sensor readings, not at any real-valued moment.
- Using the history of readings instead of the current one brings nothing: the sensor is precise (about 0.8 C
  scatter) and the outcome window is wide (40 C). An IoT challenge where the reading history matters would
  need a different outcome model.
- Events after the start (spinning, measuring) are not simulated; the case ends with the outcome.
- No "do nothing" action: a candy is always made, at the latest at the end of the window.
