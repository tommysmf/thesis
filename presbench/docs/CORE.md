# The presbench core

The core turns real cases, delivered by an adapter, into a semi-synthetic benchmark for prescriptive process
monitoring (PresPM). It is the same for every dataset. This page describes what it does, what it guarantees,
and where its limits are. To add a dataset, see [WRITING_AN_ADAPTER.md](WRITING_AN_ADAPTER.md).

## The decision the core supports

**One intervention per case, at a moment chosen during a sensor-monitored window:** "when to start, stop or
trigger X while signal S evolves". Examples: when to start spinning while a machine heats up, when to stop a
drying step, when to trigger maintenance. Each reading of the decision signal inside the window is a decision
point; the action at each point is "intervene now" or "wait"; the intervention happens at the last point at the
latest.

The decision signal may rise (heating) or fall (drying): set the adapter's `signal_direction` to +1 or -1, and
pass it to `PooledPolicy(direction=...)`.

Not supported by the core as it is (each needs a core extension, not just an adapter):

- several interventions per case, or interventions whose effects depend on each other;
- interventions that change how the signal evolves afterwards (see "How a case evolves" below);
- a "never intervene" action;
- continuous actions (intensity, dose).

## How a case evolves

The core **replays the real signal**: if a method waits, it sees the next real reading of that case. This is
valid as long as the real signal would have looked the same had the intervention not happened yet. Two
situations make that true: the signal is not affected by the intervention, or the decision window ends before
the real intervention. Anything else is a bias the adapter has to document. In the cotton candy data, spinning
slows the heating, which makes this a known, documented bias.

## What the core does, per real case

For each real case, resampled `resamples_per_case` times:

1. **Decision points.** It takes the real signal readings inside `[t_open, t_close]` (`RealCase.decision_points`).
2. **Random parts.** It draws, in this fixed order: a hidden factor u ~ N(0, 1), the policy arm (uniform number),
   and the outcome noise ~ N(0, `noise_sd`). Then the policy's own draws follow.
3. **Historical decision.** With probability `delta` it asks the adapter's historical policy. Otherwise it picks a
   uniformly random decision point, the randomized share, as in SimBank.
4. **Propensity of every decision point:** `delta * policy.distribution() + (1 - delta) / n`. The policy must
   compute `distribution()` from observable information only (see below).
5. **Outcome of every decision point.** It asks the adapter's outcome model for the expected measured outcome and
   the expected KPI at every point. If the outcome uses u, it also averages over u (9-point Gauss-Hermite) to get
   the best decision from observable information only.
6. **Output.** It writes what a method may see apart from the answer key.

The train/test split is by real case (`test_share` of the real cases, drawn with `seed`). The generator's draws
use `seed + 1`, and the online mode uses `seed + 2`.

## Guarantees (checked by tests/test_core.py)

| Guarantee | Why it matters |
|---|---|
| Nothing from `truth/` appears in `observed/` | A method cannot accidentally train on the answer key |
| The observed outcome equals the answer key at the chosen point | Log and answer key tell the same story |
| Decision points are real signal readings, and the observed data stop at the intervention | No future information leaks into the log |
| Propensities sum to 1 and match the sampling | Weighting-based methods and evaluators can be checked against the truth |
| Propensities are identical for resamples with the same observable information | They depend only on what a method can see |
| A real case is in train or test, never both | No memorizing curves |
| The online mode gives the same outcome as the generator | Online and offline evaluation agree |

## Output files

Column names use the adapter's `signal_name` (S) and `outcome_name` (O).

| File | One row per | Columns |
|---|---|---|
| `observed/event_log.csv` | event | case_id, t, timestamp, activity, O (only on the outcome event) |
| `observed/sensor_stream.csv` | signal reading up to the intervention | case_id, t, timestamp, S, extra channels |
| `observed/decision_points.csv` | decision point up to the intervention | case_id, point, t, S, started |
| `observed/cases.csv` | generated case | case_id, real_case_id, split, group, attributes..., t_open, start_point, t_start, S_at_start, O, y |
| `truth/answer_key.csv` | case x decision point (all) | case_id, point, t, S, p_start_here, expected_O, expected_y, expected_y_observable, y_if_start, is_best |
| `truth/case_truth.csv` | generated case | case_id, arm, setting, hidden, outcome info (e.g. optimum), best_point, t_best, S_best, expected_y_best, expected_y_historical, regret, best_point_observable, expected_y_best_observable, expected_y_policy_average, noise |

`y` is the KPI that methods optimize. O is the measured outcome logged in the event log. The two differ when the
KPI includes a cost (for example of waiting).

## Modules

| Module | Contents |
|---|---|
| `case.py` | `RealCase` (what an adapter delivers), `DecisionPoints` |
| `adapter.py` | `Adapter` (the contract), `AdapterParams` |
| `policies.py` | `HistoricalPolicy` interface; `threshold_point`, `delay_point`, `point_distribution`, `threshold_distribution_hidden`; `PooledPolicy` |
| `outcomes.py` | `Outcome` interface; `BellOutcome` |
| `config.py` | `CoreConfig` (core knobs), `Settings`, `make_settings` |
| `generator.py` | `generate`, `tables`, `write`, `split_cases`, `build_case` |
| `online.py` | `OnlineEnv` |
| `validation.py` | `baselines`, `naive_vs_truth`, `run`, `report` |

## Core knobs (`CoreConfig`)

| Knob | Default | Meaning |
|---|---|---|
| `delta` | 0.95 | Share decided by the historical policy; the rest is randomized (SimBank convention). 0 = randomized log |
| `noise_sd` | 0.4 | Case-level outcome noise, the same for every decision point of a case. **In the KPI's units**: the default suits cotton candy weights in grams; set it per adapter in its `realistic` scenario |
| `resamples_per_case` | 20 | Generated cases per real case. They share the real signal and attributes, so a method sees the same case at several decision points; use 1 for strictly independent cases |
| `test_share` | 0.3 | Share of real cases in the test split |
| `seed` | 0 | Random seed (split, draws) |

Adapter knobs (policy and outcome) are defined by each adapter's `Params`. `make_settings(adapter, scenario,
**overrides)` combines both, and on the command line `--set key=value` works for either.

## Data structures (reference)

**`RealCase`** (`case.py`), what `Adapter.load()` returns per usable instance:

| Field | Type | Meaning |
|---|---|---|
| `case_id` | str | Unique id of the real instance; generated case ids are `<case_id>-<rep>` |
| `group` | str | Observable grouping (batch, machine); written to cases.csv |
| `t0` | pd.Timestamp | Absolute time of t = 0; every time below is in seconds since t0 |
| `times`, `signal` | np.ndarray | Strictly increasing reading times and the decision signal at those times |
| `t_open`, `t_close` | float | Window: decision points are the readings with t_open <= t <= t_close |
| `attributes` | dict | Observable attributes, written as columns of cases.csv |
| `events` | DataFrame | Real events a method may see: columns `activity`, `t`; all t <= t_open (an event exactly at t_open is fine) |
| `channels` | dict | Optional extra sensor channels name -> (times, values), written to sensor_stream.csv (last value carried forward) |
| `info` | dict | Adapter-private (real decision, derived values); never written out. `BellOutcome.shifts` may read it |

`RealCase.decision_points()` returns **`DecisionPoints`** with `idx` (positions in `times`), `t` (s since t0),
`t_rel` (s since t_open) and `signal`. `RealCase.signal_at(t)` interpolates the signal.

**Generated cases** (the first value `generate()` returns, and what `realism()` receives as `generated`): a list
of dicts with `case_id`, `case` (the RealCase), `rep`, `split`, `dp` (DecisionPoints), `k` (historical decision
point), `arm`, `setting`, `hidden`, `pi` (propensities), `measure` and `kpi` (expected, per decision point),
`kpi_obs`, `truth_info` and `noise`.

**Tables** (the second value, and what `realism()` receives as `tables`): a dict with keys `cases`,
`decision_points`, `answer_key`, `case_truth`, `event_log`, `sensor_stream`. These are the DataFrames of the
output files below, with the same columns.

## The two interfaces an adapter implements

**Historical policy** (`policies.HistoricalPolicy`):

- `sample(case, dp, hidden, rng) -> (arm, setting, k)`: draw the historical decision point k. Use only `rng`
  for randomness.
- `distribution(case, dp) -> array`: the exact P(k) given observable information. Average over anything a
  method cannot see: unobserved settings, and u if the policy uses it.

`PooledPolicy` covers the common case. Per real case it holds a rule type (`"threshold"`: the first reading
at or above the setting; `"delay"`: the first point at least the setting in seconds after `t_open`) and a pool of
settings, one drawn uniformly. With `hidden_shift`, thresholds move by `hidden_shift * u`, and `distribution()`
integrates that out exactly. The pools must be chosen from observable information.

**Outcome** (`outcomes.Outcome`):

- `expected(case, dp, hidden) -> (measure, kpi)`: arrays over the decision points, without noise.
- `truth_info(case, hidden) -> dict`: extra columns for `case_truth.csv`.
- `uses_hidden`: True if `expected` depends on `hidden`.

`BellOutcome(height, optimum, width, width_low=0, width_high=0, shifts=(), hidden_effect=0, time_cost=0)` covers
a bell-shaped outcome in the signal at the decision point:
`measure = height * exp(-((signal - case_optimum) / width)^2)` and `kpi = measure - time_cost * t_rel`.
`width_low` and `width_high`, when non-zero, replace `width` below and above the optimum. Each entry of `shifts`
is `(name, change, center, scale)` and moves the optimum by `change * (value - center) / scale`. The value is
looked up in `case.info` first, then in `case.attributes`. So `("wear", 8.0, 30.0, 30.0)` means "+8 per 30 units
of wear above 30". The case optimum is `optimum + sum of shifts + hidden_effect * u`, and `truth_info` reports
it as `optimum`.

## Validation (`validate.py`, `presbench/validation.py`)

For any adapter, the report shows:

1. The adapter's realism checks.
2. The value of simple policies against the oracle: historical, best fixed delay, best threshold on the current
   reading, best threshold on a 10 s mean.
3. The naive confounding error, averaged over seeds.
4. The adapter's knob sweeps and scenarios.

Read it as: is it realistic, is there something to gain, does a simple rule already get it, and is there
confounding a naive method falls for?

The naive check compares the observed KPI of cases that intervened early vs late. Set `naive_contrast` to two
windows (seconds after t_open) where historical decisions actually happen. If a window holds no decisions, the
check is undefined, and the report says so instead of showing a number.

## Two linked decisions (`twostage.py`)

For "when to do A, then when to do B", where B's window and the signal seen during it depend on when A happened
(for example: when to start spinning, then when to stop). It is a separate module: the single-decision core
above is unchanged, and `twostage.py` reuses its split and random draws.

**The adapter** subclasses `TwoStageAdapter` (an `Adapter` with `stage_names` and `intervention_activities`):

| Method | Returns |
|---|---|
| `load(path)` | RealCases; `t_open`/`t_close` is the first window |
| `signal_after(case, t1)` | the signal at `case.times` if intervention 1 happened at t1; equal to the real signal up to t1 |
| `second_window(case, t1)` | `(t_open2, t_close2)`, with `t_open2 > t1` |
| `policy(cases, params)` | `(policy1, policy2)`: two `HistoricalPolicy` objects; policy 2 sees the stage-2 `DecisionPoints` (`t_rel` since `t_open2`), so `PooledPolicy` works for both |
| `outcome(params)` | a `TwoStageOutcome`: `expected(case, dp1, k1, dp2, hidden) -> (measure, kpi)` over the stage-2 points |

**Per real case** the core computes, for every first decision point k1, the signal after acting there, the
stage-2 decision points (the readings of that signal inside the second window) and the stage-2 propensities.
This is cached and shared by the resamples, since it depends on observable information only.

**Per generated case:** random parts in a fixed order (u, arm draw 1, noise, arm draw 2, then the policies' own
draws); each stage is decided by its policy with probability `delta`, else uniformly, so
`P(k1, k2) = pi1[k1] * pi2[k1][k2]`; the outcome of every path; the observable expectation (over u) if needed.

| File | One row per | Columns |
|---|---|---|
| `observed/event_log.csv` | event | real events, intervention 1, intervention 2, the outcome event |
| `observed/sensor_stream.csv` | reading up to intervention 2 | the signal as it evolved under the historical first decision |
| `observed/decision_points.csv` | decision point up to each intervention | case_id, stage, point, t, S, acted |
| `observed/cases.csv` | generated case | ..., first_point, t_first, S_at_first, second_point, t_second, S_at_second, O, y |
| `truth/answer_key.csv.gz` | case x (point1, point2) | t1, t2, S_1, S_2, p_path, expected_O, expected_y, expected_y_observable, y_if_path, is_best |
| `truth/answer_key_first.csv` | case x point1 | t1, S_1, p_first, best_point2, expected_y_best_second, expected_y_policy_second |
| `truth/case_truth.csv` | generated case | arms, settings, hidden, best path, expected_y_best, expected_y_historical, regret, expected_y_best_second_given_first, observable best, policy average, noise |

`expected_y_best_second_given_first` (the best stop after the historical start) against `expected_y_best` (the
best pair) measures what deciding the two jointly is worth. `answer_key_first.csv` gives the value of each first
decision when the second is then chosen optimally, or by the historical policy.

The answer key has one row per path (about n1 x n2 per case), so it is written compressed; keep
`resamples_per_case` low for two-stage adapters.

**Validation:** `validate.py` uses `presbench/twostage_validation.py` for two-stage adapters: the adapter's realism checks, then on the test cases historical, best second decision after the historical first, greedy (the first decision chosen as if the historical policy then decides the second, followed by the best second), best fixed delays, best thresholds and the oracle; a naive confounding check on the length of the phase between the two decisions (`naive_contrast2`); knob sweeps and scenarios. Greedy vs oracle is what deciding both together is worth.

**Online mode:** `TwoStageOnlineEnv` steps through stage 1, then stage 2 on the signal after the chosen first
decision (`obs["stage"]`, `obs["t_since_first"]`, and at the first stage-2 point the readings since
intervention 1).

**Tests:** `python tests/test_twostage.py [adapter data]` checks the same guarantees as `tests/test_core.py` for
both stages: no truth in the observed files, observed outcome = answer key at the chosen path, P(path) sums to 1
and matches the sampling, propensities depend on observables only, the split is by real case, decision points
follow the signal and the stream stops at intervention 2 (and equals the real signal up to intervention 1), and
the online mode agrees with the generator. `tests/toy_twostage.py` is the smallest two-stage adapter.
