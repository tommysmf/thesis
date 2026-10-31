"""Adapter for the TUM cotton candy dataset (Zenodo record 17226615): WHEN TO START, THEN WHEN TO STOP SPINNING.

Two linked decisions per run (presbench/twostage.py). The head temperature after any start time comes from the
heating model (adapters/cotton_candy/heating.py), fitted per run and checked on held-out readings:
  stage 1 (start): the head as if the machine were still waiting: the real readings up to the real start, then
                   the run's own waiting line. This removes the replay bias of the single start decision.
  stage 2 (stop):  the head after the chosen start: spinning from the head at that moment (batch Newton curve,
                   with the run's real residuals). The stop window runs MIN_SPIN to MAX_SPIN s after the start,
                   so a method may spin longer than the real run did.

Historical policy: the start policy of the cotton_candy adapter (fixed wait or controller, settings of comparable
real runs), then a timer: the spin duration of one of the comparable real runs of the same batch.

Outcome (weight) combines the two single-decision outcomes:
  weight = W_max * bell(head at start) * (1 - exp(-t_spin / tau)) - cold_slope * max(0, T_cold - head at stop)
with the start adapter's bell curve (specified: optimum 65 C, width 40 C, +8 C per 30 candies of wear) and the stop
adapter's spin-up and cold penalty (the cold penalty fitted on the real runs). KPI = weight - energy (the run's
real power draw times the time from "stick placed" to the stop) - thermal stress (seconds above T_stress).
The decisions interact: a colder start needs a longer spin to reach T_cold.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

from presbench import AdapterParams, RealCase
from presbench.policies import PooledPolicy
from presbench.twostage import TwoStageAdapter, TwoStageOutcome
from adapters.cotton_candy.adapter import CottonCandyAdapter, TYPICAL_POWER
from adapters.cotton_candy.heating import fit_heating, trajectory, _wait_from

MIN_SPIN, MAX_SPIN = 5.0, 120.0      # s after the start: the stop window


@dataclass
class CottonCandyJointParams(AdapterParams):
    # start: bell curve of the start adapter (specified)
    h0: float = 65.0            # C: best head temperature at the start for an average case
    w: float = 40.0             # C: width of the bell
    a_wear: float = 8.0         # C shift of the start optimum per 30 candies since maintenance
    # stop: spin-up and cold penalty of the stop adapter (cold penalty fitted)
    W_max: float = 9.3          # g: weight of a long, warm spin after an ideal start (median generated ~ real 8.6 g)
    tau: float = 5.0            # s: spin-up time constant (weakly supported)
    T_cold: float = 70.0        # C: below this head temperature at the stop the candy gets lighter (fitted)
    cold_slope: float = 0.45    # g per C below T_cold (fitted)
    # costs
    energy_price: float = 0.037  # g per Wh from "stick placed" to the stop (the run's real power draw)
    stress_price: float = 0.01  # g per second with the head above T_stress
    T_stress: float = 85.0      # C
    lam: float = 0.0            # g per s from "stick placed" to the stop: extra time cost (off)
    # hidden confounding and policy
    hidden_effect: float = 0.0  # C shift of the start optimum per unit of u
    hidden_policy: float = 0.0  # C shift of the start controller's threshold per unit of u
    pool_size: int = 3          # comparable real runs a policy setting is drawn from


class JointOutcome(TwoStageOutcome):
    def __init__(self, p, adapter):
        self.p, self.adapter = p, adapter
        self.uses_hidden = bool(p.hidden_effect)

    def start_optimum(self, case, hidden):
        p = self.p
        return p.h0 + p.a_wear * (case.attributes["wear"] - 30.0) / 30.0 + p.hidden_effect * hidden

    def expected(self, case, dp1, k1, dp2, hidden):
        p = self.p
        bell = np.exp(-((dp1.signal[k1] - self.start_optimum(case, hidden)) / p.w) ** 2)
        spin = dp2.t - dp1.t[k1]
        weight = p.W_max * bell * (1 - np.exp(-spin / p.tau)) - p.cold_slope * np.maximum(0.0, p.T_cold - dp2.signal)
        weight = np.maximum(weight, 0.0)
        since_open = dp2.t - case.t_open
        signal = self.adapter.signal_after(case, float(dp1.t[k1]))
        hot = np.concatenate([np.diff(case.times) * (signal[:-1] > p.T_stress), [0.0]])
        cum = np.concatenate([[0.0], np.cumsum(hot)])[:-1]
        stress = np.interp(dp2.t, case.times, cum) - np.interp(case.t_open, case.times, cum)
        energy = case.info["power_w"] * since_open / 3600
        kpi = weight - p.lam * since_open - p.energy_price * energy - p.stress_price * stress
        return weight, kpi

    def truth_info(self, case, hidden):
        return {"start_optimum": self.start_optimum(case, hidden)}


class CottonCandyJointAdapter(TwoStageAdapter):
    name = "cotton_candy_joint"
    signal_name = "ir_head"
    signal_unit = "C"
    signal_direction = 1
    stage_names = ("start", "stop")
    intervention_activities = ("Start spinning", "Stop spinning")
    outcome_activity = "Candy finished"
    outcome_name = "weight"
    outcome_delay = 60.0
    Params = CottonCandyJointParams
    scenarios = {
        "realistic": dict(noise_sd=0.8, resamples_per_case=5),
        "no-cold-effect": dict(noise_sd=0.8, resamples_per_case=5, cold_slope=0.0),
        "hidden-confounding": dict(noise_sd=0.8, resamples_per_case=5, hidden_effect=5.0, hidden_policy=5.0),
        # time is costly (energy 5x the default price): the start then depends on how the stop will be chosen,
        # so deciding both together is worth more than greedy (0.3 instead of 0.05)
        "costly-time": dict(noise_sd=0.8, resamples_per_case=5, energy_price=0.2),
    }
    sweeps = [("delta", [0.0, 0.5, 0.95, 1.0]), ("cold_slope", [0.0, 0.2, 0.45, 0.7]), ("w", [20.0, 40.0, 60.0]),
              ("T_cold", [65.0, 70.0, 75.0]), ("energy_price", [0.0, 0.037, 0.1, 0.2])]
    model_attributes = ["wear", "env_hum"]
    naive_contrast2 = ((40.0, 60.0), (70.0, 95.0))   # s of spinning: stop after 40-60 s vs after 70-95 s

    # ---- data -------------------------------------------------------------------------------------
    def load(self, path, verbose=True):
        base = CottonCandyAdapter().load(path, verbose=False)
        fits = fit_heating(base)
        cases = []
        for c in base:
            fit, a, b = fits[c.case_id], c.info["t_real_start"], c.info["t_real_end"]
            waiting = c.signal.astype(float).copy()          # the head as if the machine kept waiting
            later = c.times > a
            waiting[later] = _wait_from(fit, c, c.times[later], True)
            px, pw = c.info["power"]
            m = (px >= c.t_open) & (px <= b)
            power = float(np.mean(pw[m])) if m.any() else TYPICAL_POWER
            cases.append(RealCase(
                case_id=c.case_id, group=c.group, t0=c.t0, times=c.times, signal=waiting,
                t_open=c.t_open, t_close=c.t_close, attributes=c.attributes, events=c.events,
                channels=c.channels, info=dict(c.info, real=c, heating=fit, power_w=power,
                                               real_spin=b - a)))
        if verbose:
            print(f"loaded {len(cases)} usable cases (from the cotton_candy adapter, with heating fits)")
        return cases

    def signal_after(self, case, t1):
        """Real readings up to the earlier of t1 and the real start, then the heating model."""
        return trajectory(case.info["real"], case.info["heating"], t1)

    def second_window(self, case, t1):
        return t1 + MIN_SPIN, t1 + MAX_SPIN

    # ---- historical policy ------------------------------------------------------------------------
    def policy(self, cases, params):
        start = CottonCandyAdapter().policy([c.info["real"] for c in cases], params)
        kinds, pools = {}, {}
        for c in cases:
            cand = sorted([o for o in cases if o.group == c.group],
                          key=lambda o: (abs(o.attributes["wear"] - c.attributes["wear"]), int(o.case_id)))
            kinds[c.case_id] = "delay"
            pools[c.case_id] = [max(o.info["real_spin"] - MIN_SPIN, 0.0) for o in cand[:params.pool_size]]
        stop = PooledPolicy(kinds, pools, arms={k: "timer" for k in kinds}, direction=self.signal_direction)
        return start, stop

    def outcome(self, params):
        return JointOutcome(params, self)

    # ---- realism checks (validate.py) -------------------------------------------------------------
    def realism(self, cases, generated, tables):
        pct = lambda s: tuple(float(v) for v in np.percentile(s, [10, 50, 90]).round(1))
        c = tables["cases"].merge(tables["case_truth"][["case_id", "arm1", "arm2"]], on="case_id")
        h = c[(c.arm1 != "random") & (c.arm2 != "random")]
        real = [x.info["real"] for x in cases]
        real_w = [x.info["real_weight"] for x in cases if 3 < x.info["real_weight"] < 20]
        return [
            ("wait after stick placed (s)", pct(h.t_first - h.t_open), pct([x.info["real_wait"] for x in cases])),
            ("spin duration (s)", pct(h.t_second - h.t_first), pct([x.info["real_spin"] for x in cases])),
            ("head at start (C)", pct(h.ir_head_at_first), pct([r.signal_at(r.info["t_real_start"]) for r in real])),
            ("head at stop (C)", pct(h.ir_head_at_second), pct([r.signal_at(r.info["t_real_end"]) for r in real])),
            ("observed weight (g)", pct(c.weight), pct(real_w)),
        ]

    def realism_notes(self, cases, generated, tables):
        f = tables["answer_key_first"]
        k = tables["answer_key"][["case_id", "point1", "point2", "t2"]]
        f = f[f.case_id.str.endswith("-000")].merge(k, left_on=["case_id", "point1", "best_point2"],
                                                    right_on=["case_id", "point1", "point2"])
        f = f.assign(spin=f.t2 - f.t1)
        bins = [0, 55, 60, 65, 70, 75, 80, 100]
        b = f.groupby(pd.cut(f.ir_head_1, bins), observed=False).spin.median()
        rho = f[["ir_head_1", "spin"]].corr(method="spearman").iloc[0, 1]
        return ["", "How the decisions interact: the best spin length after each possible start, by the head "
                    f"temperature at that start (one resample per run; Spearman {rho:+.2f}).", "",
                "| Head at start (C) | " + " | ".join(str(i) for i in b.index) + " |", "|---" * (len(b) + 1) + "|",
                "| Best spin (s, median) | " + " | ".join("-" if np.isnan(v) else f"{v:.0f}" for v in b) + " |"]


ADAPTER = CottonCandyJointAdapter()
