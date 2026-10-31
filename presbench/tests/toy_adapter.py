"""Tiny synthetic adapters: they let the core be tested without any real dataset, and show the smallest
complete adapter. ToyAdapter: a machine heating up linearly with noise, read every 2-5 s (rising signal).
ToyFallingAdapter: a product drying, moisture falling (falling signal)."""
from dataclasses import dataclass
import numpy as np
import pandas as pd

from presbench import Adapter, AdapterParams, RealCase
from presbench.policies import PooledPolicy
from presbench.outcomes import BellOutcome


@dataclass
class ToyParams(AdapterParams):
    optimum: float = 60.0
    width: float = 15.0
    wear_shift: float = 5.0
    time_cost: float = 0.01
    hidden_effect: float = 0.0
    hidden_policy: float = 0.0


class ToyAdapter(Adapter):
    name = "toy"
    signal_name = "temp"
    signal_unit = "C"
    intervention_activity = "Start"
    outcome_activity = "Done"
    outcome_name = "quality"
    outcome_delay = 30.0
    Params = ToyParams
    scenarios = {"realistic": {}, "hidden": dict(hidden_effect=4.0, hidden_policy=4.0)}
    model_attributes = ["wear"]

    def load(self, path=None, verbose=True, n=40):
        rng = np.random.default_rng(123)
        cases = []
        for i in range(n):
            dt = [2.0, 3.0, 5.0][i % 3]                      # irregular sampling between cases
            times = np.arange(0, 180, dt)
            rate = rng.uniform(0.15, 0.35)
            signal = 30 + rate * times + rng.normal(0, 0.5, len(times))
            events = pd.DataFrame({"activity": ["Switch on", "Load"], "t": [0.0, 10.0]})
            cases.append(RealCase(case_id=str(1000 + i), group=f"g{i % 4}", t0=pd.Timestamp("2026-01-01", tz="UTC"),
                                  times=times, signal=signal, t_open=10.0, t_close=150.0,
                                  attributes=dict(wear=float(rng.integers(0, 60))), events=events,
                                  info=dict(rate=rate)))
        return cases

    def policy(self, cases, params):
        kinds = {c.case_id: ("threshold" if int(c.case_id) % 2 else "delay") for c in cases}
        pools = {c.case_id: ([50.0, 55.0, 60.0] if kinds[c.case_id] == "threshold" else [20.0, 40.0, 80.0])
                 for c in cases}
        return PooledPolicy(kinds, pools, hidden_shift=params.hidden_policy, direction=self.signal_direction)

    def outcome(self, params):
        return BellOutcome(height=10.0, optimum=params.optimum, width=params.width,
                           shifts=[("wear", params.wear_shift, 30.0, 30.0)], hidden_effect=params.hidden_effect,
                           time_cost=params.time_cost)


class ToyFallingAdapter(ToyAdapter):
    """The same, mirrored: the signal falls (like moisture while drying) and the threshold is reached from above."""
    name = "toy_falling"
    signal_name = "moisture"
    signal_unit = "%"
    signal_direction = -1

    def load(self, path=None, verbose=True, n=40):
        cases = super().load(path, verbose, n)
        for c in cases:
            c.signal = 100.0 - c.signal          # 70 -> about 20 %
        return cases

    def policy(self, cases, params):
        pol = super().policy(cases, params)
        pol.pools = {cid: ([100.0 - v for v in p] if pol.kinds[cid] == "threshold" else p) for cid, p in pol.pools.items()}
        return pol

    def outcome(self, params):
        return BellOutcome(height=10.0, optimum=100.0 - params.optimum, width=params.width,
                           shifts=[("wear", -params.wear_shift, 30.0, 30.0)], hidden_effect=params.hidden_effect,
                           time_cost=params.time_cost)


ADAPTER = ToyAdapter()
FALLING = ToyFallingAdapter()
