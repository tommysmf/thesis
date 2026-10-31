# Cotton candy adapter: when to stop spinning

Same data as `adapters/cotton_candy/` (see its README for the dataset and the preparation script); a different
decision. The real runs, their real start and stop times and the drop rules come from the `cotton_candy`
adapter; this adapter moves the window to the spinning phase.

```
python generate.py --adapter cotton_candy_stop --data ../datasets/cotton-candy/processed --out output/cc_stop
python validate.py --adapter cotton_candy_stop --data ../datasets/cotton-candy/processed
python adapters/cotton_candy_stop/test_adapter.py ../datasets/cotton-candy/processed
```

In the core's tables, `start_point`, `t_start` and `ir_head_at_start` describe the moment of the intervention,
which here is the **stop**.

## Answers to the adapter questions (docs/WRITING_AN_ADAPTER.md, step 2)

| # | Question | Answer for this decision |
|---|---|---|
| 1 | Case, unusable instances | One candy run. 167 usable: the 171 of the `cotton_candy` adapter minus 4 with a spinning phase shorter than 20 s |
| 2 | Decision signal | Infrared head temperature (`ir_head`), read every 1.3-6.5 s. It keeps rising while spinning (median 0.22 C/s) |
| 3 | Window | Opens at the real start of spinning, closes at the real stop (median 73 s) |
| 4 | Real intervention | The real stop: the end of "Create Cotton Candy" (start + cooking time, + ~7 s in batches 0-14) |
| 5 | Does the intervention change the signal? | Not inside the window: waiting means "keep spinning", which is what the real machine did until its real stop. **Replaying the real signal is valid**, unlike for the start decision. The price: a method can never spin longer than the real run did |
| 6 | Who decided | A timer: the cooking time is set before spinning, mostly the same within a batch. Modelled with `PooledPolicy` (delay rule): the spin duration of one of the 3 runs of the same batch nearest in wear |
| 7 | Events a method may see | The setup events and "Start spinning". **Left out:** "Set cooking time", which reveals the real stop |
| 8 | Observable attributes | Batch, wear, ambient temperature and humidity, head temperature at the start, seconds waited before the start |
| 9 | KPI | Weight minus the energy used while spinning minus thermal stress. The weight model is **partly fitted** (below) |

## The outcome, and what is fitted

`weight = W_max * (1 - exp(-t_spin / tau)) - cold_slope * max(0, T_cold - head at the stop)`

- **Cold penalty (fitted).** Over the 147 runs with a valid weight, no variable explains the weight overall,
  but within a batch the head temperature at the stop does: Spearman 0.30 (p = 0.0002), and still 0.27 after
  controlling for spin time, start temperature and wear. A hinge fit with batch fixed effects is best at
  `T_cold` = 70 C with 0.45 g per C below it (95% bootstrap CI 0.32-0.57; within-batch R^2 0.22; 0.43 g/C without
  the 7 most extreme weights). Other candidate targets (size, firmness, cooldown time, carry-over to the next
  run) showed no link that survives a batch control.
- **Spin-up (weakly supported).** `tau` = 5 s: weight is nearly complete after ~15 s. Only four real runs spun
  less than 40 s (5-20 s, 6.7-8.0 g), so this is mostly specified.
- **Costs (measured, priced by choice).** Energy: the real power trace while spinning (~970 W) at
  0.037 g per Wh (= 0.01 g/s, as the start adapter's time cost). Thermal stress: seconds with the head above
  85 C, from the real head trace, at 0.01 g per second (chosen).
- `W_max` = 8.9 g sets the median generated weight to the real 8.6 g; `noise_sd` = 0.8 g in the scenarios is the
  residual sd of the real weights after the fit (0.84 g).

The trade-off this creates: stopping early saves energy and thermal stress, but a cold head costs weight. The
best stop depends on how warm the head was at the start and how fast it heats, so it differs per case.

## Overlap: most historical stops are at the window's end

The window ends at the real stop, and runs of the same batch mostly had the same cooking time, so a drawn
setting is usually at least as long as the run's own spin: about 87% of the timer arm stops at the last decision
point. Earlier stops in the observed log come from shorter neighbours and the randomized share (1 - `delta`).
This is a real feature of the data (no operator ever stopped early on sight), and it makes learning harder:
`delta` is the knob to study it.

## Knobs (`CottonCandyStopParams`)

| Knob | Default | Meaning |
|---|---|---|
| `W_max`, `tau` | 8.9 g, 5 s | Weight of a long warm spin; spin-up time constant |
| `T_cold`, `cold_slope` | 70 C, 0.45 g/C | Cold penalty (fitted) |
| `energy_price` | 0.037 g/Wh | Energy cost while spinning (real power trace) |
| `stress_price`, `T_stress` | 0.01 g/s, 85 C | Thermal stress cost |
| `lam` | 0 | Extra time cost per second spun |
| `hidden_effect` | off | Shift of `T_cold` per unit of the hidden factor u |
| `pool_size` | 3 | Comparable real runs per policy setting |

Scenarios: `realistic`, `no-cold-effect` (cold_slope 0), `no-stress` (stress_price 0), `hidden-confounding`
(T_cold shifts 5 C per unit of u). All use `noise_sd` = 0.8.

## Open decisions (for the supervisors)

Thermal stress as a cost, and its price; whether to model spinning beyond the real stop (needs a heating model);
a two-decision version (start and stop together), which needs a core extension.
