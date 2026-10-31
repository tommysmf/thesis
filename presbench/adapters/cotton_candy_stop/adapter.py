"""Adapter for the TUM cotton candy dataset (Zenodo record 17226615): WHEN TO STOP SPINNING.

Decision: when to stop spinning while the head keeps heating. Decision signal: the infrared head temperature.
The window is the real spinning phase, from the real start to the real stop. Waiting means "keep spinning",
which is exactly what the real machine did until its real stop, so replaying the real signal is valid here
(unlike for the start decision, see adapters/cotton_candy/README.md).

The real runs are read by the cotton_candy adapter (same real start and stop times, same drop rules); this
adapter moves the window to the spinning phase and has its own policy and outcome.

Outcome (weight), partly fitted on the real runs:
  weight = W_max * (1 - exp(-t_spin / tau)) - cold_slope * max(0, T_cold - head at the stop)
The cold penalty is fitted with batch fixed effects: below about 70 C at the stop, each degree costs about
0.45 g (95% CI 0.32-0.57 g). tau is only weakly supported (the four runs that spun 5-20 s weighed 6.7-8.0 g).
KPI = weight - energy_price * Wh used while spinning (real power trace) - stress_price * seconds above T_stress
(thermal stress on the machine, from the real head trace).
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

from presbench import Adapter, AdapterParams, RealCase
from presbench.outcomes import Outcome
from presbench.policies import PooledPolicy
from adapters.cotton_candy.adapter import CottonCandyAdapter, energy_used, SETUP_ACTIVITIES

MIN_SPIN = 20.0                 # s: shortest usable spinning phase (= window)
START_ACTIVITY = "Start spinning"


@dataclass
class CottonCandyStopParams(AdapterParams):
    # weight = W_max * (1 - exp(-t_spin/tau)) - cold_slope * max(0, T_cold + hidden_effect*u - head at stop)
    W_max: float = 8.9          # g: weight of a long, warm spin (sets the median generated weight to the real 8.6 g)
    tau: float = 5.0            # s: spin-up time constant (weakly supported: 5-20 s spins still gave 6.7-8.0 g)
    T_cold: float = 70.0        # C: below this head temperature at the stop the candy gets lighter (fitted)
    cold_slope: float = 0.45    # g per C below T_cold (fitted with batch fixed effects; 95% CI 0.32-0.57)
    energy_price: float = 0.037  # g per Wh used while spinning (real power trace; ~970 W = 0.01 g/s)
    stress_price: float = 0.01  # g per second with the head above T_stress (thermal stress; chosen)
    T_stress: float = 85.0      # C: head temperature counted as thermal stress
    lam: float = 0.0            # g per s spun: extra time cost (off; the energy cost already grows with time)
    hidden_effect: float = 0.0  # C shift of T_cold per unit of the hidden factor u (0 = off)
    pool_size: int = 3          # comparable real runs a policy setting is drawn from (same batch, nearest in wear)


def seconds_above(case, t, level):
    """Seconds with the real head reading above `level`, from t_open to t (each reading holds until the next)."""
    x, s = case.times, case.signal
    hot = np.concatenate([np.diff(x) * (s[:-1] > level), [0.0]])
    cum = np.concatenate([[0.0], np.cumsum(hot)])[:-1]          # seconds above before each reading
    at = lambda v: np.interp(v, x, cum)
    return at(np.asarray(t, dtype=float)) - at(case.t_open)


class StopOutcome(Outcome):
    """Weight builds up during the first seconds of spinning and is lower when the head is still cold at the stop.
    The KPI pays for the energy used and the time spent above T_stress while spinning."""

    def __init__(self, p):
        self.p = p
        self.uses_hidden = bool(p.hidden_effect)

    def t_cold(self, hidden):
        return self.p.T_cold + self.p.hidden_effect * hidden

    def expected(self, case, dp, hidden):
        p, t = self.p, np.asarray(dp.t_rel, dtype=float)
        head = np.asarray(dp.signal, dtype=float)
        weight = p.W_max * (1 - np.exp(-t / p.tau)) - p.cold_slope * np.maximum(0.0, self.t_cold(hidden) - head)
        weight = np.maximum(weight, 0.0)
        kpi = (weight - p.lam * t - p.energy_price * energy_used(case, dp.t)
               - p.stress_price * seconds_above(case, dp.t, p.T_stress))
        return weight, kpi

    def truth_info(self, case, hidden):
        return {"T_cold": self.t_cold(hidden)}


class CottonCandyStopAdapter(Adapter):
    name = "cotton_candy_stop"
    signal_name = "ir_head"
    signal_unit = "C"
    signal_direction = 1                 # the head keeps heating while spinning
    intervention_activity = "Stop spinning"
    outcome_activity = "Candy finished"
    outcome_name = "weight"
    outcome_delay = 60.0
    Params = CottonCandyStopParams
    scenarios = {
        "realistic": dict(noise_sd=0.8),             # residual sd of the real weights after the fit: 0.84 g
        "no-cold-effect": dict(noise_sd=0.8, cold_slope=0.0),
        "no-stress": dict(noise_sd=0.8, stress_price=0.0),
        "hidden-confounding": dict(noise_sd=0.8, hidden_effect=5.0),
    }
    sweeps = [("delta", [0.0, 0.5, 0.95, 1.0]), ("cold_slope", [0.0, 0.2, 0.45, 0.7]),
              ("T_cold", [65.0, 70.0, 75.0]), ("stress_price", [0.0, 0.01, 0.03])]
    model_attributes = ["wear", "env_hum", "head_at_start"]
    naive_contrast = ((35.0, 55.0), (65.0, 90.0))   # s after the real start: stop after 35-55 s vs 65-90 s

    # ---- data -------------------------------------------------------------------------------------
    def load(self, path, verbose=True):
        base = CottonCandyAdapter().load(path, verbose=False)
        cases, dropped = [], {}
        for c in base:
            a, b = c.info["t_real_start"], c.info["t_real_end"]
            n = int(np.sum((c.times >= a) & (c.times <= b)))
            if b - a < MIN_SPIN or n < 5:
                dropped["spinning phase too short"] = dropped.get("spinning phase too short", 0) + 1
                continue
            # events a method may see: the setup before "stick placed" and the real start (the start is not
            # the decision here); "Set cooking time" stays out, it reveals the real stop
            ev = c.events[c.events.activity.isin(SETUP_ACTIVITIES)]
            ev = pd.concat([ev, pd.DataFrame([{"activity": START_ACTIVITY, "t": a}])], ignore_index=True)
            cases.append(RealCase(
                case_id=c.case_id, group=c.group, t0=c.t0, times=c.times, signal=c.signal, t_open=a, t_close=b,
                attributes=dict(c.attributes, head_at_start=c.signal_at(a), waited=a - c.t_open),
                events=ev, channels=c.channels, info=dict(c.info, real_spin=b - a)))
        if verbose:
            print(f"loaded {len(cases)} usable cases ({len(base)} from the cotton_candy adapter); dropped: {dropped}")
        return cases

    # ---- historical policy ------------------------------------------------------------------------
    def policy(self, cases, params):
        """A timer, as in the real runs (the cooking time is set before spinning): the spin duration of one of the
        `pool_size` real runs of the same batch nearest in wear. Batch and wear are observable."""
        kinds, pools = {}, {}
        for c in cases:
            cand = [o for o in cases if o.group == c.group]
            cand = sorted(cand, key=lambda o: (abs(o.attributes["wear"] - c.attributes["wear"]), int(o.case_id)))
            kinds[c.case_id] = "delay"
            pools[c.case_id] = [o.info["real_spin"] for o in cand[:params.pool_size]]
        return PooledPolicy(kinds, pools, arms={k: "timer" for k in kinds}, direction=self.signal_direction)

    # ---- outcome ----------------------------------------------------------------------------------
    def outcome(self, params):
        return StopOutcome(params)

    # ---- realism checks (validate.py) -------------------------------------------------------------
    def realism(self, cases, generated, tables):
        pct = lambda s: tuple(float(v) for v in np.percentile(s, [10, 50, 90]).round(1))
        c = tables["cases"].merge(tables["case_truth"][["case_id", "arm"]], on="case_id")
        h = c[c.arm == "timer"]
        real_w = [x.info["real_weight"] for x in cases if 3 < x.info["real_weight"] < 20]
        return [
            ("timer arm: spin duration (s)", pct(h.t_start - h.t_open), pct([x.info["real_spin"] for x in cases])),
            ("timer arm: head at the stop (C)", pct(h.ir_head_at_start),
             pct([x.signal_at(x.info["t_real_end"]) for x in cases])),
            ("observed weight (g)", pct(c.weight), pct(real_w)),
        ]

    def realism_notes(self, cases, generated, tables):
        d = pd.DataFrame([(x.group, x.signal_at(x.info["t_real_end"]), x.info["real_weight"]) for x in cases],
                         columns=["batch", "h", "w"])
        d = d[(d.w > 3) & (d.w < 15)]
        d["dev"] = d.w - d.groupby("batch").w.transform("mean")
        c = tables["cases"].merge(tables["case_truth"][["case_id", "arm"]], on="case_id")
        g = c[c.arm == "timer"].copy()
        g["dev"] = g.weight - g.groupby("group").weight.transform("mean")
        bins = [0, 65, 70, 75, 80, 85, 105]
        rb = d.groupby(pd.cut(d.h, bins), observed=False).dev.agg(["mean", "size"])
        gb = g.groupby(pd.cut(g.ir_head_at_start, bins), observed=False).dev.mean()
        share_last = float(np.mean([gc["k"] == len(gc["dp"]) - 1 for gc in generated if gc["arm"] == "timer"]))
        return ["", f"Timer arm: share of historical stops at the last decision point (the real stop): "
                    f"{share_last:.2f}. The window ends at the real stop, so a setting longer than the run's own "
                    f"spin stops there.", "",
                "Weight minus its batch mean, by head reading at the stop (real runs vs generated historical cases).",
                "The cold penalty is fitted on the real runs, so these should agree roughly.", "",
                "| Head at stop | " + " | ".join(str(i) for i in rb.index) + " |", "|---" * (len(rb) + 1) + "|",
                "| Real (g) | " + " | ".join(f"{m:+.2f} (n={n})" for m, n in zip(rb["mean"], rb["size"])) + " |",
                "| Generated (g) | " + " | ".join(f"{v:+.2f}" for v in gb) + " |"]


ADAPTER = CottonCandyStopAdapter()
