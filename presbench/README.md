# presbench: semi-synthetic PresPM benchmarks from IoT-enriched event logs

Prescriptive process monitoring (PresPM) methods cannot be evaluated on real logs alone: a log shows one
decision per case, never what another decision would have given. presbench turns a real IoT-enriched event log
into a **semi-synthetic benchmark**. The real cases and sensor signals are kept, the historical decision policy
and the outcome are specified, and the outcome of every possible decision is stored in an answer key.

The code is split in two:

- **Core** (`presbench/`): the same for every dataset. It draws historical decisions with a randomized
  share, computes exact propensities, builds the answer key, writes observed/ and truth/, and provides an online
  mode, validation and tests. See [docs/CORE.md](docs/CORE.md).
- **Adapters** (`adapters/<name>/`): one per dataset. An adapter reads the data, says where the decision is,
  what the historical policy was and what the outcome is. See
  [docs/WRITING_AN_ADAPTER.md](docs/WRITING_AN_ADAPTER.md) and the template in `adapters/_template/`.

Supported decision type: **one intervention per case, timed during a sensor-monitored window** ("when to
start / stop / trigger X while signal S evolves"). Decision points are the real sensor readings, so decisions
happen between process events. **Two linked decisions per case** ("when to start, then when to stop") are
supported by `presbench/twostage.py`; see [docs/CORE.md](docs/CORE.md#two-linked-decisions-twostagepy).

| Adapter | Dataset | Decision |
|---|---|---|
| `cotton_candy` | TUM cotton candy machine (Zenodo 17226615) | When to start spinning while the head heats up |
| `cotton_candy_stop` | Same data | When to stop spinning (window = the real spinning phase; partly fitted outcome) |
| `cotton_candy_joint` | Same data | When to start, then when to stop (two linked decisions; heating model) |
| `tests/toy_adapter.py` | Synthetic (for tests) | When to start while a machine heats up |

## Quick start

```
pip install numpy pandas
python generate.py --adapter cotton_candy --data ../datasets/cotton-candy/processed --out output/cc
python validate.py --adapter cotton_candy --data ../datasets/cotton-candy/processed
python demo.py     --adapter cotton_candy --data ../datasets/cotton-candy/processed
python tests/test_core.py                                                    # core, on synthetic data
python tests/test_twostage.py                                                # two-decision core, synthetic data
python tests/test_core.py cotton_candy ../datasets/cotton-candy/processed    # core, on an adapter
python adapters/cotton_candy/test_adapter.py ../datasets/cotton-candy/processed
```

Options: `--scenario NAME` (named settings defined by the adapter) and `--set key=value` (any core or adapter
knob, for example `--set delta=0` for a randomized log or `--set resamples_per_case=1` for one case per real case).

## Layout

```
presbench/            core (see docs/CORE.md)
adapters/
  cotton_candy/       adapter.py, README.md (dataset semantics), test_adapter.py
  _template/          skeleton for a new adapter
docs/                 CORE.md, WRITING_AN_ADAPTER.md
tests/                test_core.py (core guarantees, any adapter), toy_adapter.py
generate.py, validate.py, demo.py
```

Generated data (`output/`) is not committed; the same settings and seed always give the same data.

This replaces `cc_generator`: on the cotton candy data it produces identical output for the same settings
(checked table by table).
