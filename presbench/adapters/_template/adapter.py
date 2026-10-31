"""Adapter template: copy this folder to adapters/<name>/ and fill in every TODO.

Read docs/WRITING_AN_ADAPTER.md first, and answer its step-2 questions on the data before writing code.
Check with:  python tests/test_core.py <name> <data path>
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

from presbench import Adapter, AdapterParams, RealCase
from presbench.policies import PooledPolicy
from presbench.outcomes import BellOutcome


@dataclass
class TemplateParams(AdapterParams):
    # TODO: the knobs of your policy and outcome, with defaults and a comment on where each value comes from
    optimum: float = 0.0        # signal value of the best decision for an average case (specified)
    width: float = 1.0          # how forgiving the outcome is around the optimum
    height: float = 1.0         # best possible outcome
    time_cost: float = 0.0      # KPI cost per second waited after the window opens
    hidden_effect: float = 0.0  # hidden confounding: shift of the optimum per unit of u (0 = off)
    hidden_policy: float = 0.0  # hidden confounding: shift of the policy threshold per unit of u (0 = off)


class TemplateAdapter(Adapter):
    name = "template"                       # TODO: folder name
    signal_name = "signal"                  # TODO: column name of the decision signal, e.g. "temperature"
    signal_unit = ""                        # TODO
    signal_direction = 1                    # TODO: +1 if the signal rises during the window, -1 if it falls
    intervention_activity = "Intervene"     # TODO: activity inserted at the chosen decision point
    outcome_activity = "Outcome measured"   # TODO
    outcome_name = "outcome"                # TODO: e.g. "weight", "yield"
    outcome_delay = 0.0                     # TODO: s between intervention and outcome (cosmetic)
    Params = TemplateParams
    # "realistic" holds your defaults; set noise_sd there, in your KPI's units
    scenarios = {"realistic": dict(noise_sd=0.4), "hidden-confounding": dict(noise_sd=0.4, hidden_effect=1.0,
                                                                              hidden_policy=1.0)}
    sweeps = [("delta", [0.0, 0.5, 0.95, 1.0])]
    model_attributes = []                   # TODO: numeric attributes a simple regression may use

    def load(self, path, verbose=True):
        """TODO: read the dataset, return one RealCase per usable instance, in a stable order."""
        cases, dropped = [], {}
        # for each instance:
        #   t0      = the absolute time t = 0 refers to (pd.Timestamp)
        #   times   = sorted seconds since t0 of the decision signal readings (np.ndarray)
        #   signal  = the readings (np.ndarray)
        #   t_open  = first moment the intervention is possible; t_close = last decision point
        #   events  = DataFrame(activity, t) of real events up to t_open that a method may see
        #   attributes = observable case attributes; group = observable grouping (batch, machine, ...)
        #   info    = what really happened (real intervention time, real setting, ...), never written out
        #   cases.append(RealCase(case_id=..., group=..., t0=..., times=..., signal=..., t_open=..., t_close=...,
        #                         attributes={...}, events=..., info={...}))
        if verbose:
            print(f"loaded {len(cases)} usable cases; dropped: {dropped}")
        return cases

    def policy(self, cases, params):
        """TODO: the historical policy. With PooledPolicy: per case a rule type ("threshold" on the signal or
        "delay" in s after t_open) and a pool of real settings, chosen from OBSERVABLE information only."""
        kinds = {c.case_id: "threshold" for c in cases}
        pools = {c.case_id: [c.signal_at(c.info["t_real"])] for c in cases}   # e.g. the real decision's signal value
        return PooledPolicy(kinds, pools, hidden_shift=params.hidden_policy, direction=self.signal_direction)

    def outcome(self, params):
        """TODO: the outcome model. BellOutcome: best around `optimum`, shifted by attributes via `shifts`."""
        return BellOutcome(height=params.height, optimum=params.optimum, width=params.width,
                           shifts=[],  # e.g. [("wear", 8.0, 30.0, 30.0)]: +8 per 30 units of wear above 30
                           hidden_effect=params.hidden_effect, time_cost=params.time_cost)

    def realism(self, cases, generated, tables):
        """Optional: (quantity, generated, real) rows comparing the generated data with the real data."""
        return []


ADAPTER = TemplateAdapter()
