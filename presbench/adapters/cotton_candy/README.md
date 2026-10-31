# Cotton candy adapter

Data: [Cotton Candy XES YAML](https://zenodo.org/records/17226615) (TUM, 2025), parsed into `runs.csv`,
`sensors.csv` and `events.csv` by `datasets/cotton-candy/prepare_cotton_candy.py` (in the thesis repository).
Download the dataset from Zenodo, unzip it into `datasets/cotton-candy/`, and run that script. Credit the
authors and follow the license stated on the Zenodo page.

```
python generate.py --adapter cotton_candy --data ../datasets/cotton-candy/processed --out output/cc
python adapters/cotton_candy/test_adapter.py ../datasets/cotton-candy/processed
```

## Answers to the adapter questions (docs/WRITING_AN_ADAPTER.md, step 2)

| # | Question | Answer for this dataset |
|---|---|---|
| 1 | Case, unusable instances | One candy run. 171 of 185 usable. Dropped: 12 where the create step does not match the rule below (aborted or inconsistent), 1 without timestamps, 1 with too short a window |
| 2 | Decision signal | Infrared head temperature (`ir_head`). Read every 1.3, 2.3, 4.3 or 6.5 s depending on the batch, regular within a run |
| 3 | Window | Opens at "Place the Wood Stick in Center". Closes at the hottest point within 120 s, never after the real spinning ended (the real machine cools afterwards) |
| 4 | Real intervention | Batches 0-14: "Create Cotton Candy" + the configured waiting time (the step lasts waiting time + cooking time + about 7 s). Batches 15-23: "Create Cotton Candy" itself (the waiting time is ignored; the step lasts the cooking time) |
| 5 | Does the intervention change the signal? | **Yes, a little.** Pooled over runs, the head heats 0.27 C/s before the real start and 0.17 C/s after it at 65-75 C, but that compares different runs. Within the same run (heating model below) spinning heats at 0.89 times the waiting rate (IQR 0.77-1.09; 0.83 for starts at 65-75 C). About two thirds of the decision points lie after the real start, so the replayed "waiting" signal rises somewhat too slowly there. **Known, documented bias** |
| 6 | Who decided | Batches 0-14: a waiting time per run. Cold machines (head below 40 C at "stick placed") waited about 105 s, then the settings swept downwards with wear. Batches 15-23: a warm-up loop started at a head temperature of about 65 C (batches 15-17) or 52-57 C (19-23), skipped when the head was already warm. Modelled with `PooledPolicy`: settings from the 3 most comparable real runs (same batch, same cold/warm machine, nearest in wear) |
| 7 | Events a method may see | Sugar amount set, sugar filled, machine on, stick number set, stick placed. **Left out:** "Set waiting time" and "Set cooking time", which reveal the real decision |
| 8 | Observable attributes | Batch (`group`), iterations since maintenance (`wear`), ambient temperature and humidity at "stick placed" |
| 9 | KPI | Weight minus 0.01 g per second waited (the time cost is a choice). The real weights barely depend on the start temperature (8.2-8.8 g in every 5 C band, one 17.4 g outlier excluded), so the outcome is **specified**: a wide bell curve (optimum 65 C, width 40 C, +8 C per 30 candies of wear). Scenario `energy` replaces the time cost by the **real energy used** after "stick placed" (power trace of the run, 0.037 g per Wh) |

## Energy cost (scenario `energy`)

The power meter is logged every 1.3-6.5 s. In the decision window the heater draws an almost constant power:
median 970 W per run (runs differ by about 15 W; within a run the sd is about 2 W), and the same after the
real start (spinning adds no measurable power). So replaying the real power trace is unbiased, unlike the head
temperature, and the energy cost of waiting is close to linear in time (about 0.27 Wh per second). With
0.037 g/Wh it matches the default time cost of 0.01 g/s, and the validation numbers are the same; the gain is
that the cost of waiting is measured instead of chosen. The power is also written to `sensor_stream.csv` as the
`power` channel, so methods can see the energy used so far.

## Heating model (`heating.py`), for start and stop together

One decision can replay the real signal; a start and a stop together cannot, because after a counterfactual
start the head spins while the real run was waiting, or the other way round. `heating.py` simulates the head
for any start time; `validate_heating.py` checks it on held-out readings and writes
[heating_report.md](heating_report.md). It is not used by the single-decision adapters.

- **Waiting:** a straight line with the run's own slope (median 0.23 C/s; 135 runs), else its batch's median
  slope (36 runs with too few waiting readings). A Newton curve's ceiling hits its bound for almost every run,
  and the line forecasts better (second half of the phase from the first: 0.7 C off after 40 s, batch slope
  1.1 C).
- **Spinning:** Newton's law of heating, `dT/dt = k (T_inf - T)`, with `T_inf` and `k` fitted jointly over the
  run's batch (each run with its own starting level; all runs for 4 runs whose batch fit is degenerate). Fitted
  without the run, it forecasts the second half of the spinning phase 1.5 C off after 40 s with almost no bias,
  better than the run's own curve (2.4 C) or a straight line (2.6 C), and predicts the whole spinning phase from
  the real head at the start within 1.0-1.9 C RMSE in every start-temperature band.
- **Real readings where valid:** before the earlier of the real and the simulated start; with the real start,
  up to the real stop. The real residuals around the fit are added back, so the simulated signal keeps the real
  noise and the real, irregular reading times.

## Knobs (`CottonCandyParams`)

| Knob | Default | Meaning |
|---|---|---|
| `W_max`, `h0`, `w` | 9.3 g, 65 C, 40 C | Height, optimum and width of the outcome curve |
| `w_cold`, `w_hot` | off | Different widths below / above the optimum |
| `a_wear`, `b_humidity` | 8 C, 0 | Optimum shift per 30 candies of wear / per SD of humidity |
| `lam` | 0.01 g/s | Time cost in the KPI |
| `energy_price` | off | Energy cost in the KPI per Wh used after "stick placed" (real power trace) |
| `hidden_effect`, `hidden_policy` | off | Hidden confounding: shift of the optimum / controller threshold per unit of u |
| `pool_size` | 3 | Comparable real runs per policy setting |

Scenarios: `realistic`, `hidden-confounding` (5 C / 5 C), `asymmetric` (14 C below, 34 C above the optimum),
`energy` (no time cost; 0.037 g per Wh of real energy use).

## Open decisions (for the supervisors)

KPI with a chosen time cost or the measured energy cost (scenario `energy`); replaying the signal after the real start (bias above) or using the heating
model; the outcome model (bell curve or a physical model); resamples vs one case per run.
