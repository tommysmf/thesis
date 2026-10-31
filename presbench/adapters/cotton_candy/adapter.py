"""Adapter for the TUM cotton candy dataset (Zenodo record 17226615).

Decision: when to start spinning while the machine heats up. Decision signal: the infrared head temperature.

Input: the folder written by datasets/cotton-candy/prepare_cotton_candy.py (runs.csv, sensors.csv, events.csv).

How the real process starts spinning (checked on the data; see README.md in this folder):
  * batches 0-14: "Create Cotton Candy" first waits the configured `wait_time`, then spins for `cook_time`
    (the step lasts wait_time + cook_time + ~7 s). Spin start = create_calling + wait_time.
  * batches 15-23: the waiting time setting is ignored (the step lasts cook_time). A warm-up loop
    ("Run until CC Head is optimally warm") polls the head temperature BEFORE "Create Cotton Candy" and is
    skipped when the head is already warm; spinning starts at create_calling.
"""
from dataclasses import dataclass
import os
import numpy as np
import pandas as pd

from presbench import Adapter, AdapterParams, RealCase
from presbench.policies import PooledPolicy
from presbench.outcomes import BellOutcome

TS = dict(utc=True, format="ISO8601", errors="coerce")
# real activities kept in the generated log (setup before spinning); the real "Set waiting/cooking time"
# events are left out on purpose: they reveal the REAL operator's decision
SETUP_ACTIVITIES = ["Set the Sugar Amount for Size", "Fill Machine with Sugar", "Turn the Machine On",
                    "Set the Stick Number", "Place the Wood Stick in Center"]
READY_ACTIVITY = "Place the Wood Stick in Center"   # spinning can start once the stick is placed
CONTROLLER_ACTIVITY = "Run until CC Head is optimally warm"
FIRST_CONTROLLER_BATCH = 15     # from this batch on, a temperature controller decides the start
PEAK_SMOOTH_S = 10.0            # s: smoothing used only to find the temperature peak that ends the window
COLD_HEAD = 40.0                # degC: a head below this when the stick is placed counts as a cold machine
MIN_WINDOW, MAX_WINDOW = 20.0, 120.0   # s: shortest usable window; longest window after "stick placed"
TYPICAL_POWER = 970.0           # W: median real power draw in the window, used for a run without power readings


@dataclass
class CottonCandyParams(AdapterParams):
    # outcome: weight = W_max*exp(-((head - h_opt)/w)^2), h_opt = h0 + a_wear*(wear-30)/30 + b_humidity*z(hum)
    W_max: float = 9.3          # g: best possible weight (sets the median generated weight to the real 8.6 g)
    h0: float = 65.0            # degC: optimal head temperature for an average case (specified)
    w: float = 40.0             # degC: width of the window (wide: the real weights are almost flat)
    w_cold: float = 0.0         # degC: width below the optimum (0 = use w)
    w_hot: float = 0.0          # degC: width above the optimum (0 = use w)
    a_wear: float = 8.0         # degC per 30 candies since maintenance (worn machines need a hotter head)
    b_humidity: float = 0.0     # degC per standard deviation of ambient humidity (off)
    lam: float = 0.01           # g per s waited after "stick placed": the time cost in the KPI
    energy_price: float = 0.0   # g per Wh used after "stick placed" (real power trace): the energy cost (off)
    hidden_effect: float = 0.0  # degC shift of the optimum per unit of the hidden factor u
    hidden_policy: float = 0.0  # degC shift of the controller threshold per unit of u
    pool_size: int = 3          # comparable real runs a policy setting is drawn from (nearest in wear)


def _smooth(x, v, width):
    """Centred moving average over a time window (works for irregular readings)."""
    lo = np.searchsorted(x, x - width / 2)
    hi = np.searchsorted(x, x + width / 2, side="right")
    c = np.concatenate([[0.0], np.cumsum(v)])
    return (c[hi] - c[lo]) / (hi - lo)


class EnergyBellOutcome(BellOutcome):
    """BellOutcome whose KPI also pays for the energy used between "stick placed" and the start:
    kpi -= energy_price * Wh, from the real power trace of the run (case.info["power"]). The heater draws an
    almost constant ~970 W in the window, also after the real start, so replaying the trace is unbiased."""

    def __init__(self, energy_price=0.0, **kw):
        super().__init__(**kw)
        self.energy_price = energy_price

    def expected(self, case, dp, hidden):
        measure, kpi = super().expected(case, dp, hidden)
        if self.energy_price:
            kpi = kpi - self.energy_price * energy_used(case, dp.t)
        return measure, kpi


def energy_used(case, t):
    """Wh used from t_open to t (s since t0): the integral of the real power trace (or TYPICAL_POWER)."""
    x, p = case.info.get("power", (np.array([]), np.array([])))
    t = np.asarray(t, dtype=float)
    if len(x) < 2:
        return TYPICAL_POWER * (t - case.t_open) / 3600
    cum = np.concatenate([[0.0], np.cumsum(np.diff(x) * (p[1:] + p[:-1]) / 2)])   # W*s since the first reading
    at = lambda v: np.interp(v, x, cum) + p[0] * np.minimum(v - x[0], 0) + p[-1] * np.maximum(v - x[-1], 0)
    return (at(t) - at(case.t_open)) / 3600


class CottonCandyAdapter(Adapter):
    name = "cotton_candy"
    signal_name = "ir_head"
    signal_unit = "C"
    signal_direction = 1                 # the head heats up
    intervention_activity = "Start spinning"
    outcome_activity = "Candy finished"
    outcome_name = "weight"
    outcome_delay = 150.0
    Params = CottonCandyParams
    scenarios = {
        "realistic": {},
        "hidden-confounding": dict(hidden_effect=5.0, hidden_policy=5.0),
        "asymmetric": dict(w_cold=14.0, w_hot=34.0),
        # the time cost replaced by the real energy use: 0.037 g/Wh at ~970 W is about the default 0.01 g/s
        "energy": dict(lam=0.0, energy_price=0.037),
    }
    sweeps = [("delta", [0.0, 0.5, 0.95, 1.0]), ("w", [20.0, 30.0, 40.0, 60.0]), ("h0", [60.0, 65.0, 70.0]),
              ("a_wear", [0.0, 8.0, 16.0])]
    model_attributes = ["wear", "env_hum"]
    naive_contrast = ((0.0, 4.0), (10.0, 40.0))   # s after "stick placed": start at once vs wait 10-40 s

    # ---- data -------------------------------------------------------------------------------------
    def load(self, path, verbose=True):
        runs = pd.read_csv(os.path.join(path, "runs.csv"))
        sensors = pd.read_csv(os.path.join(path, "sensors.csv"))
        events = pd.read_csv(os.path.join(path, "events.csv"))
        for c in ["machine_on_done", "create_calling", "create_done"]:
            runs[c] = pd.to_datetime(runs[c], **TS)
        sensors["ts"] = pd.to_datetime(sensors["ts"], **TS)
        events["time"] = pd.to_datetime(events["time"], **TS)
        controller_runs = set(events.loc[events.activity == CONTROLLER_ACTIVITY, "instance"])

        cases, dropped = [], {}

        def drop(reason):
            dropped[reason] = dropped.get(reason, 0) + 1

        for _, run in runs.iterrows():
            if pd.isna(run.machine_on_done) or pd.isna(run.create_calling) or pd.isna(run.create_done):
                drop("no machine-on or create times"); continue
            t0 = run.machine_on_done
            controller = int("".join(ch for ch in str(run.batch) if ch.isdigit()) or 0) >= FIRST_CONTROLLER_BATCH
            wait = 0.0 if controller else max(float(run.wait_time), 0.0)
            create_s = (run.create_done - run.create_calling).total_seconds()
            if abs(create_s - (wait + run.cook_time)) > (12 if controller else 20):   # aborted or inconsistent
                drop("create step does not match wait + cook time"); continue
            t_real_start = (run.create_calling - t0).total_seconds() + wait
            t_real_end = (run.create_done - t0).total_seconds()
            ev = events[events.instance == run.instance].copy()
            ev["t"] = (ev.time - t0).dt.total_seconds()
            ready = ev[(ev.activity == READY_ACTIVITY) & (ev.t >= 0) & (ev.t <= t_real_start)]
            if ready.empty:
                drop("no stick placement before the start"); continue
            t_ready = float(ready.t.max())
            s = sensors[sensors.instance == run.instance].copy()
            s["x"] = (s.ts - t0).dt.total_seconds()
            hs = s[s.ir_head.notna()].sort_values("x").drop_duplicates("x")
            if len(hs) < 20:
                drop("too few head readings"); continue
            x, head = hs.x.to_numpy(), hs.ir_head.to_numpy()
            smooth = _smooth(x, head, PEAK_SMOOTH_S)
            # window end: the hottest (smoothed) point, but never after the real spinning ended
            # (later the real machine cools down) and at most MAX_WINDOW after the stick is placed
            lim = min(t_ready + MAX_WINDOW, t_real_end)
            m = (x >= t_ready) & (x <= lim)
            if m.sum() < 5:
                drop("heating window too short"); continue
            t_end = float(x[m][int(np.argmax(smooth[m]))])
            if t_end - t_ready < MIN_WINDOW:
                drop("heating window too short"); continue
            env = s[s.env_temp.notna() & (s.x <= t_ready)]
            if env.empty:
                env = s[s.env_temp.notna()].head(3)
            env_temp = float(env.env_temp.mean()) if len(env) else np.nan
            env_hum = float(env.env_hum.mean()) if len(env) else np.nan
            setup = ev[ev.activity.isin(SETUP_ACTIVITIES) & (ev.t >= -90) & (ev.t <= t_ready)]
            setup = setup.sort_values("t").drop_duplicates("activity", keep="last")[["activity", "t"]]
            head_at_ready = float(np.interp(t_ready, x, head))
            pw = s[s.power.notna()].sort_values("x").drop_duplicates("x")
            power = (pw.x.to_numpy(), pw.power.to_numpy(float))
            cases.append(RealCase(
                case_id=str(int(run.instance)), group=run.batch, t0=t0, times=x, signal=head,
                t_open=t_ready, t_close=t_end,
                attributes=dict(wear=float(run.iteration_since_maintenance), env_temp=env_temp, env_hum=env_hum),
                events=setup.reset_index(drop=True),
                channels=dict(env_temp=(np.array([0.0]), [env_temp]), env_hum=(np.array([0.0]), [env_hum]),
                              power=power),
                info=dict(power=power, t_real_start=t_real_start, t_real_end=t_real_end, real_controller=controller,
                          loop_ran=run.instance in controller_runs, real_wait=t_real_start - t_ready,
                          head_at_ready=head_at_ready, cold=head_at_ready < COLD_HEAD,
                          real_weight=float(run.weight) if pd.notna(run.weight) else np.nan)))

        # humidity as a z-score over all usable cases (missing -> average)
        hum = np.array([c.attributes["env_hum"] for c in cases])
        mu, sd = np.nanmean(hum), np.nanstd(hum)
        for c in cases:
            h = c.attributes["env_hum"]
            c.info["hum_z"] = 0.0 if np.isnan(h) else (h - mu) / sd
        if verbose:
            print(f"loaded {len(cases)} usable cases from {len(runs)} runs; dropped: {dropped}")
        return cases

    # ---- historical policy ------------------------------------------------------------------------
    def policy(self, cases, params):
        """What the real operators did, with the setting drawn from the `pool_size` most comparable real runs:

        batches 0-14 (fixed waiting time): real waits of runs in the same batch with the same cold/warm machine
        (cold machines: the waits of all cold starts, about 105 s), nearest in wear;
        batches 15-23 (controller): real start temperatures of runs in the same batch where the warm-up loop
        polled, nearest in wear. Batch, machine temperature at "stick placed" and wear are all observable.
        """
        kinds, pools, arms = {}, {}, {}
        for c in cases:
            ci = c.info
            if ci["real_controller"]:
                cand = [o for o in cases if o.info["real_controller"] and o.info["loop_ran"] and o.group == c.group]
                value = lambda o: o.signal_at(o.info["t_real_start"])
                kinds[c.case_id], arms[c.case_id] = "threshold", "controller"
            elif ci["cold"]:
                cand = [o for o in cases if not o.info["real_controller"] and o.info["cold"]]
                value = lambda o: o.info["real_wait"]
                kinds[c.case_id], arms[c.case_id] = "delay", "fixed_wait"
            else:
                cand = [o for o in cases if not o.info["real_controller"] and not o.info["cold"] and o.group == c.group]
                value = lambda o: o.info["real_wait"]
                kinds[c.case_id], arms[c.case_id] = "delay", "fixed_wait"
            cand = sorted(cand, key=lambda o: (abs(o.attributes["wear"] - c.attributes["wear"]), int(o.case_id)))
            pools[c.case_id] = [value(o) for o in cand[:params.pool_size]]
        return PooledPolicy(kinds, pools, arms, hidden_shift=params.hidden_policy, direction=self.signal_direction)

    # ---- outcome ----------------------------------------------------------------------------------
    def outcome(self, params):
        return EnergyBellOutcome(energy_price=params.energy_price, height=params.W_max, optimum=params.h0,
                                 width=params.w, width_low=params.w_cold, width_high=params.w_hot,
                                 shifts=[("wear", params.a_wear, 30.0, 30.0), ("hum_z", params.b_humidity, 0.0, 1.0)],
                                 hidden_effect=params.hidden_effect, time_cost=params.lam)

    # ---- realism checks (validate.py) -------------------------------------------------------------
    def realism(self, cases, generated, tables):
        pct = lambda s: tuple(float(v) for v in np.percentile(s, [10, 50, 90]).round(1))
        c = tables["cases"].merge(tables["case_truth"][["case_id", "arm"]], on="case_id")
        c["wait"] = c.t_start - c.t_open
        loop = [x for x in cases if x.info["real_controller"] and x.info["loop_ran"]]
        fixed = [x for x in cases if not x.info["real_controller"]]
        ctrl = [x for x in cases if x.info["real_controller"]]
        real_w = [x.info["real_weight"] for x in cases if 3 < x.info["real_weight"] < 20]
        return [
            ("controller arm: head reading at start (C)", pct(c[c.arm == "controller"].ir_head_at_start),
             pct([x.signal_at(x.info["t_real_start"]) for x in loop])),
            ("controller arm: wait after stick placed (s)", pct(c[c.arm == "controller"].wait),
             pct([x.info["real_wait"] for x in ctrl])),
            ("fixed-wait arm: wait after stick placed (s)", pct(c[c.arm == "fixed_wait"].wait),
             pct([x.info["real_wait"] for x in fixed])),
            ("observed weight (g)", pct(c.weight), pct(real_w)),
        ]

    def realism_notes(self, cases, generated, tables):
        c = tables["cases"].merge(tables["case_truth"][["case_id", "arm"]], on="case_id")
        f = c[c.arm == "fixed_wait"]
        hr = {x.case_id: x.info["head_at_ready"] for x in cases}
        gen = np.corrcoef(f.real_case_id.map(hr), f.t_start - f.t_open)[0, 1]
        fr = [x for x in cases if not x.info["real_controller"]]
        real = np.corrcoef([x.info["head_at_ready"] for x in fr], [x.info["real_wait"] for x in fr])[0, 1]
        bins = [0, 55, 60, 65, 70, 75, 80, 95]
        rw = pd.DataFrame([(x.signal_at(x.info["t_real_start"]), x.info["real_weight"]) for x in cases],
                          columns=["h", "w"])
        rw = rw[(rw.w > 3) & (rw.w < 15)]           # 17.4 g (run 64570) is an outlier
        rb = rw.groupby(pd.cut(rw.h, bins), observed=False).w.agg(["mean", "size"])
        g = c[c.arm != "random"]
        gb = g.groupby(pd.cut(g.ir_head_at_start, bins), observed=False).weight.mean()
        return ["", f"Fixed-wait arm, correlation between head temperature at \"stick placed\" and waiting time: "
                    f"generated {gen:+.2f}, real {real:+.2f} (cold machines wait longer).", "",
                "Mean weight by head reading at the start (real runs, one 17.4 g outlier excluded, vs generated",
                "historical cases). The outcome is specified, not fitted; this is a sanity check only.", "",
                "| Head at start | " + " | ".join(str(i) for i in rb.index) + " |", "|---" * (len(rb) + 1) + "|",
                "| Real (g) | " + " | ".join(f"{m:.2f} (n={n})" for m, n in zip(rb["mean"], rb["size"])) + " |",
                "| Generated (g) | " + " | ".join(f"{v:.2f}" for v in gb) + " |"]


ADAPTER = CottonCandyAdapter()
