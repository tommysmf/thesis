# Cotton candy adapter: when to start, then when to stop spinning

Two linked decisions per run, on the same data as `adapters/cotton_candy/` (dataset and preparation script: see
its README). It uses the two-stage core (`presbench/twostage.py`, described in
[docs/CORE.md](../../docs/CORE.md#two-linked-decisions-twostagepy)) and the heating model
(`adapters/cotton_candy/heating.py`, validated in [heating_report.md](../cotton_candy/heating_report.md)).

```
python generate.py --adapter cotton_candy_joint --data ../datasets/cotton-candy/processed --out output/cc_joint
python tests/test_twostage.py cotton_candy_joint ../datasets/cotton-candy/processed
python adapters/cotton_candy_joint/test_adapter.py ../datasets/cotton-candy/processed
```

## How a run evolves

| Phase | Signal a method sees | Source |
|---|---|---|
| Stage 1: from "stick placed" until the start | the head as if the machine kept waiting | real readings up to the real start, then the run's own waiting line |
| Stage 2: from the start until the stop (5-120 s after it) | the head while spinning, from the head at the chosen start | real readings if the start is the real one (up to the real stop); otherwise the batch's spinning curve with the run's real residuals |

So, unlike the single start decision, stage 1 has **no replay bias**: after the real start the method sees the
waiting head, not the real spinning one. And unlike the single stop decision, a method can spin **longer** than
the real run did. The price is that part of the observed signal is simulated (validated: 0.7-1.5 C off 40 s
ahead, see the heating report).

## Historical policy

- Start: the `cotton_candy` adapter's policy (fixed wait for batches 0-14, temperature controller for 15-23,
  settings of the 3 most comparable real runs).
- Stop: a timer, the spin duration of one of the 3 runs of the same batch nearest in wear.

## Outcome and KPI

`weight = W_max * bell(head at start) * (1 - exp(-t_spin / tau)) - cold_slope * max(0, T_cold - head at stop)`

- `bell`: the start adapter's curve (specified: optimum 65 C, width 40 C, +8 C per 30 candies of wear).
- Spin-up (`tau` = 5 s, weakly supported) and cold penalty (0.45 g per C below 70 C, **fitted**): the stop adapter's.
- KPI = weight - 0.037 g per Wh of the run's real power draw from "stick placed" to the stop - 0.01 g per second
  with the head above 85 C. `noise_sd` = 0.8 g, `W_max` = 9.3 g (median generated weight 8.5-8.7 g, real 8.6 g).

**The decisions interact:** a colder start needs a longer spin to get the head above `T_cold`. The best spin
after a given start falls from about 77 s (head below 55 C at the start) to about 21 s (above 80 C);
Spearman -0.89 between the head at the start and the best spin length.

## Validation ([validation_report_cotton_candy_joint.md](../../validation_report_cotton_candy_joint.md))

Test cases, mean expected KPI over seeds 0-2 (all scored with the answer key):

| Policy | KPI |
|---|---|
| historical (start and stop) | 7.25 |
| best fixed delays (wait d1, then spin d2; open-loop) | 7.31 |
| historical start, best stop after it | 7.77 |
| best thresholds (start at head >= T1, stop at head >= T2 after >= m s) | 8.33 |
| greedy (start as if the historical timer stops it, then the best stop) | 8.43 |
| oracle (best start and stop together) | 8.48 |

- **Sensor-based rules beat fixed timings by a lot** (8.33 vs 7.31): the right spin depends on how warm the head
  was at the start, which a fixed timing cannot see.
- **Deciding both jointly adds little over greedy** in the default setting (0.05). The decisions interact in
  *what* to do (best spin vs head at start, Spearman -0.89) but hardly in *value*, because the start bell curve
  is flat and waiting is cheap. The joint gain grows with the cost of time: 0.17 at `energy_price` 0.1 and 0.31
  at 0.2 (validation report, section 3). The scenario `costly-time` (below) sets 0.2 for experiments where the
  sequence itself should matter.
- Confounding: the naive estimate of the effect of a longer spin is 0.40 too low (about 0 on a randomized log).

Generated vs real (p10 / median / p90): wait after "stick placed" 3.9 / 33 / 91 s vs 2.8 / 33 / 95 s; spin 53 /
75 / 93 s vs 51 / 73 / 90 s; head at start 54 / 67 / 77 C vs 54 / 67 / 78 C; head at stop 69 / 79 / 94 C vs 68 /
78 / 93 C.

## Size

About 2,300 (start, stop) paths per run: with 5 resamples per real run (the scenarios' default) the answer key
has about 2 million rows (88 MB compressed). Generating and writing takes about 30 s.

## Knobs (`CottonCandyJointParams`)

| Knob | Default | Meaning |
|---|---|---|
| `h0`, `w`, `a_wear` | 65 C, 40 C, 8 C | Start bell curve and its shift with wear |
| `W_max`, `tau` | 9.3 g, 5 s | Weight of a long warm spin after an ideal start; spin-up time |
| `T_cold`, `cold_slope` | 70 C, 0.45 g/C | Cold penalty at the stop (fitted) |
| `energy_price` | 0.037 g/Wh | Energy from "stick placed" to the stop |
| `stress_price`, `T_stress` | 0.01 g/s, 85 C | Thermal stress |
| `lam` | 0 | Extra time cost |
| `hidden_effect`, `hidden_policy` | off | Hidden confounding: start optimum / controller threshold per unit of u |
| `pool_size` | 3 | Comparable real runs per policy setting |

Scenarios: `realistic`, `no-cold-effect` (the decisions then interact only through the spin-up and the costs),
`hidden-confounding` (5 C / 5 C), `costly-time` (below). All use `noise_sd` = 0.8 and 5 resamples per run.

**`costly-time`**: energy at 0.2 g per Wh (5 times the default; about 0.054 g per second of waiting or spinning),
a stand-in for any setting where machine time is expensive. The start then depends on how the stop will be
chosen, so the sequence matters (test cases, seeds 0-2):

| Policy | KPI |
|---|---|
| historical | 2.24 |
| best fixed delays (wait 20-30 s, spin 30 s) | 4.13 |
| historical start, best stop after it | 4.41 |
| best thresholds (start at about 62 C, stop at about 69 C after at least 20 s) | 5.45 |
| greedy | 5.48 |
| oracle | 5.79 |

Deciding both together is worth 0.32 +- 0.01 over greedy here (0.05 in `realistic`), and the best simple rules
fall 0.34 short of the oracle. The KPI is lower overall because every second costs more; compare policies within
a scenario, not across.

## Open decisions (for the supervisors)

Whether a partly simulated signal is acceptable (the alternative, replaying the real signal, cannot represent a
start and a stop together); the start bell curve is still specified, not fitted; thermal stress price.
