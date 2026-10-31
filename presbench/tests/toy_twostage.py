"""Tiny synthetic two-stage adapter, to test presbench/twostage.py without a real dataset: a machine heats up
linearly while waiting; after "Start" it heats more slowly; the second decision is when to "Stop". The outcome
needs a warm start AND a long enough, warm enough second phase, so the best stop depends on the start."""
from dataclasses import dataclass
import numpy as np
import pandas as pd

from presbench import AdapterParams, RealCase
from presbench.policies import PooledPolicy
from presbench.twostage import TwoStageAdapter, TwoStageOutcome


@dataclass
class ToyTwoParams(AdapterParams):
    optimum: float = 55.0       # best signal at the start
    width: float = 15.0
    t_ramp: float = 10.0        # s: second phase needed to build the outcome
    warm: float = 70.0          # below this signal at the stop the outcome drops
    cold_slope: float = 0.3
    time_cost: float = 0.01     # per second since t_open, until the stop
    hidden_effect: float = 0.0  # shift of the start optimum per unit of u
    hidden_policy: float = 0.0  # shift of the stage-1 threshold per unit of u


class ToyOutcome(TwoStageOutcome):
    def __init__(self, p):
        self.p, self.uses_hidden = p, bool(p.hidden_effect)

    def expected(self, case, dp1, k1, dp2, hidden):
        p = self.p
        start = np.exp(-((dp1.signal[k1] - p.optimum - p.hidden_effect * hidden) / p.width) ** 2)
        d = dp2.t - dp1.t[k1]
        measure = 10 * start * (1 - np.exp(-d / p.t_ramp)) - p.cold_slope * np.maximum(0, p.warm - dp2.signal)
        return measure, measure - p.time_cost * (dp2.t - case.t_open)


class ToyTwoStageAdapter(TwoStageAdapter):
    name = "toy_twostage"
    signal_name = "temp"
    signal_unit = "C"
    stage_names = ("start", "stop")
    intervention_activities = ("Start", "Stop")
    outcome_activity = "Done"
    outcome_name = "quality"
    outcome_delay = 20.0
    Params = ToyTwoParams
    scenarios = {"realistic": {}, "hidden": dict(hidden_effect=4.0, hidden_policy=4.0)}

    def load(self, path=None, verbose=True, n=30):
        rng = np.random.default_rng(321)
        cases = []
        for i in range(n):
            dt = [2.0, 3.0, 5.0][i % 3]
            times = np.arange(0, 300, dt)
            rate = rng.uniform(0.2, 0.35)
            noise = rng.normal(0, 0.4, len(times))
            cases.append(RealCase(
                case_id=str(2000 + i), group=f"g{i % 3}", t0=pd.Timestamp("2026-01-01", tz="UTC"),
                times=times, signal=30 + rate * times + noise, t_open=10.0, t_close=120.0,
                attributes=dict(wear=float(rng.integers(0, 60))),
                events=pd.DataFrame({"activity": ["Switch on", "Load"], "t": [0.0, 10.0]}),
                info=dict(rate=rate, noise=noise)))
        return cases

    def signal_after(self, case, t1):
        """Before t1 the real signal; after t1 it heats at 60% of the rate, from the signal at t1 (same noise)."""
        rate, noise = case.info["rate"], case.info["noise"]
        s = case.signal.copy()
        after = case.times > t1
        s[after] = case.signal_at(t1) + 0.6 * rate * (case.times[after] - t1) + noise[after]
        return s

    def second_window(self, case, t1):
        return t1 + 5.0, t1 + 90.0

    def policy(self, cases, params):
        kinds = {c.case_id: ("threshold" if int(c.case_id) % 2 else "delay") for c in cases}
        pools = {c.case_id: ([45.0, 50.0, 55.0] if kinds[c.case_id] == "threshold" else [10.0, 30.0, 60.0])
                 for c in cases}
        first = PooledPolicy(kinds, pools, hidden_shift=params.hidden_policy, direction=self.signal_direction)
        second = PooledPolicy({c.case_id: "delay" for c in cases}, {c.case_id: [20.0, 40.0, 60.0] for c in cases})
        return first, second

    def outcome(self, params):
        return ToyOutcome(params)


ADAPTER = ToyTwoStageAdapter()
