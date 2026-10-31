# Writing an adapter for a new dataset

An adapter tells the core everything specific to one dataset: how to read it, where the decision is, what
the historical policy was, and what the outcome is. The core does the rest (see [CORE.md](CORE.md)).
Start from `adapters/_template/adapter.py`. `adapters/cotton_candy/` is a complete example, and
`tests/toy_adapter.py` is the smallest one.

Most mistakes happen in steps 1 and 2, not in the code. In the cotton candy dataset, misreading when the real
intervention happened took four review rounds to get right. Write your answers down in the adapter's README.

## Step 1: Does the dataset fit?

You need, per case:

- an **event log** (activities with timestamps) and
- at least one **sensor signal** recorded during the phase where the decision would be taken, and
- a **moment that can plausibly be chosen**: start, stop or trigger something while the signal evolves.

The core supports one such intervention per case. If the intervention changes the signal afterwards (see
step 2, question 5), or there are several interdependent interventions, the core needs extending first.

## Step 2: Answer these questions on the data, before writing code

| # | Question | Where it goes |
|---|---|---|
| 1 | What is one case? Which instances are unusable (aborted, missing timestamps or sensors) and why? | `load()`; print the drop reasons |
| 2 | Which signal drives the decision, and how often is it read? Regular or irregular? Does it rise or fall during the window? | `RealCase.times`, `signal`, `signal_direction` |
| 3 | When does the window open (first moment the intervention is possible) and close (last moment)? | `t_open`, `t_close` |
| 4 | When did the real intervention happen? Check it against the durations and settings in the log, not only against event names | `info` (for the policy and realism checks) |
| 5 | Does the intervention change the signal? Compare the rate of change before and after the real intervention **at the same signal level** (raw slopes mislead, because rates change with the level anyway). If it does, replaying the real signal after the real intervention is biased: document it, or close the window at the real intervention | README; possibly `t_close` |
| 6 | Who decided, and how? A timer, a controller, an operator? Did the rule change between batches, or depend on the machine state? | `policy()` |
| 7 | Which events before the window may a method see, and which would reveal the real decision (for example a logged setting)? Leave the latter out | `RealCase.events` |
| 8 | Which case attributes are observable (machine, wear, environment)? | `RealCase.attributes`, `group` |
| 9 | What is the KPI? Does the real outcome depend on the decision at all? Usually it barely does, so the outcome is specified, not fitted: say so | `outcome()` |

## Step 3: Implement the adapter

Copy `adapters/_template/` to `adapters/<name>/`, including its empty `__init__.py`, and fill it in. The
data structures are listed in [CORE.md](CORE.md#data-structures-reference).

- **Class attributes:** `name`, `signal_name`, `signal_unit`, `signal_direction` (+1 rising, -1 falling),
  `intervention_activity`, `outcome_activity`, `outcome_name`, `outcome_delay`.
- **`Params`:** a dataclass with the adapter's knobs (policy and outcome), with defaults.
- **`load(path)`:** returns a list of `RealCase`. Keep a stable order, since resampling and seeds depend on it.
  Times are in seconds since `t0`. Put adapter-private facts, such as the real intervention time or derived
  values, in `info`; they never reach the observed data.
- **`policy(cases, params)`:** returns a `HistoricalPolicy`. With `PooledPolicy`, give each real case a rule
  type and a pool of real settings chosen from **observable** information only (group, attributes, the signal
  before the window). That keeps `distribution()` a valid propensity. Write a `HistoricalPolicy` subclass for
  anything else; its `distribution()` must be exact.
- **`outcome(params)`:** returns an `Outcome`. `BellOutcome` covers "best around some signal value, optimum
  shifting with attributes". Write an `Outcome` subclass for anything else.
- **Scenarios:** the `realistic` scenario holds your defaults and may set core knobs too. In particular, set
  `noise_sd` there: it is in your KPI's units, and the core default (0.4) suits grams of cotton candy.
- **Optional:** `sweeps` (knobs for validate.py), `model_attributes` (attributes the demo regression may use),
  `naive_contrast` (two waiting windows, in seconds after t_open, where historical decisions actually happen), and
  `realism(cases, generated, tables)` / `realism_notes(...)` (generated vs real comparisons; the arguments are
  described in CORE.md).

## Step 4: Test and validate

```
python tests/test_core.py <name> <data path>       # the core guarantees on your data
python validate.py --adapter <name> --data <data path> --quick   # seconds: realism and baselines only
python validate.py --adapter <name> --data <data path>           # minutes: over 3 seeds, with sweeps and scenarios
python demo.py --adapter <name> --data <data path>
```

Add adapter-specific tests in `adapters/<name>/test_adapter.py`, especially for the answers to step 2 (for
example "the real intervention time equals X" on every case).

In the validation report, check:

- **Realism:** the historical decisions and outcome scale look like the real ones.
- **Headroom:** the oracle beats the historical policy clearly.
- **Difficulty:** how much of the gap a simple threshold already closes.
- **Confounding:** the naive error at `delta` 0 (should be about 0) vs 0.95.

## Things the core does not do for you

- Decide whether replaying the real signal is valid (question 5).
- Tell you whether the specified outcome is plausible. Compare it with the real outcome per signal band, but
  expect the real data to be confounded and often flat.
- Find leaks in the events you keep (question 7).
