"""Load the real cotton candy runs (output of prepare_cotton_candy.py) as heating curves.

Each usable run becomes a Curve: the real head-temperature trajectory, the real setup events
before spinning, and the case attributes. Everything the generator does is built on these.
"""
from dataclasses import dataclass
import os
import numpy as np
import pandas as pd

TS = dict(utc=True, format="ISO8601", errors="coerce")
# real activities kept in the generated log (setup before spinning); real "Set waiting/cooking time"
# events are left out on purpose: they reveal the REAL operator's decision
SETUP_ACTIVITIES = ["Set the Sugar Amount for Size", "Fill Machine with Sugar", "Turn the Machine On",
                    "Set the Stick Number", "Place the Wood Stick in Center"]
READY_ACTIVITY = "Place the Wood Stick in Center"   # spinning can start once the stick is placed


@dataclass
class Curve:
    curve_id: int              # real run instance id
    batch: str
    machine_on: pd.Timestamp   # real absolute time of t = 0
    t_ready: float             # s: stick placed, first possible start
    t_real_start: float        # s: when the real run started spinning
    t_end: float               # s: first temperature peak = last decision point
    x: np.ndarray              # s since machine on, raw head readings
    head: np.ndarray           # degC, raw infrared head temperature
    env_temp: float            # degC, ambient temperature (mean before the real start)
    env_hum: float             # %, ambient humidity (mean before the real start)
    wear: float                # iterations since maintenance
    setup_events: pd.DataFrame # columns activity, t (real setup before t_ready)

    def waiting_head(self, t, slowdown, stretch=1.0):
        """Head temperature at times t if spinning has NOT started yet.

        Before the real start this is the real reading. After it, the real curve heats ~25% too fast
        (it was recorded while spinning), so only `slowdown` of each further increase is kept.
        `stretch` scales all heating after t_ready (resampling variety; 1 = real).
        """
        t = np.asarray(t, dtype=float)
        h = np.interp(t, self.x, self.head)
        h_rs = np.interp(self.t_real_start, self.x, self.head)
        h = np.where(t <= self.t_real_start, h, h_rs + slowdown * (h - h_rs))
        h_ready = np.interp(self.t_ready, self.x, self.head)
        return h_ready + stretch * (h - h_ready)


def load_curves(processed_dir, min_window=20.0, verbose=True):
    runs = pd.read_csv(os.path.join(processed_dir, "runs.csv"))
    sensors = pd.read_csv(os.path.join(processed_dir, "sensors.csv"))
    events = pd.read_csv(os.path.join(processed_dir, "events.csv"))
    for c in ["machine_on_done", "create_calling"]:
        runs[c] = pd.to_datetime(runs[c], **TS)
    sensors["ts"] = pd.to_datetime(sensors["ts"], **TS)
    events["time"] = pd.to_datetime(events["time"], **TS)

    curves, dropped = [], {}
    def drop(reason):
        dropped[reason] = dropped.get(reason, 0) + 1

    for _, run in runs.iterrows():
        if pd.isna(run.machine_on_done) or pd.isna(run.create_calling):
            drop("no machine-on or start time"); continue
        t0 = run.machine_on_done
        t_real_start = (run.create_calling - t0).total_seconds()
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
        # last decision point = first temperature peak within 300 s after ready (smoothed)
        win = hs[(hs.x >= t_ready) & (hs.x <= t_ready + 300)]
        if len(win) < 10:
            drop("heating window too short"); continue
        sm = win.ir_head.rolling(5, center=True, min_periods=1).mean().to_numpy()
        t_end = float(win.x.to_numpy()[int(np.argmax(sm))])
        if t_end - t_ready < min_window:
            drop("heating window too short"); continue
        env = s[s.env_temp.notna() & (s.x <= t_real_start)]
        setup = ev[ev.activity.isin(SETUP_ACTIVITIES) & (ev.t >= -90) & (ev.t <= t_ready)]
        setup = setup.sort_values("t").drop_duplicates("activity", keep="last")[["activity", "t"]]
        curves.append(Curve(
            curve_id=int(run.instance), batch=run.batch, machine_on=t0, t_ready=t_ready,
            t_real_start=t_real_start, t_end=t_end, x=hs.x.to_numpy(), head=hs.ir_head.to_numpy(),
            env_temp=float(env.env_temp.mean()) if len(env) else np.nan,
            env_hum=float(env.env_hum.mean()) if len(env) else np.nan,
            wear=float(run.iteration_since_maintenance), setup_events=setup.reset_index(drop=True)))

    # humidity as a z-score over all usable curves (missing -> average)
    hum = np.array([c.env_hum for c in curves])
    mu, sd = np.nanmean(hum), np.nanstd(hum)
    for c in curves:
        c.hum_z = 0.0 if np.isnan(c.env_hum) else (c.env_hum - mu) / sd
    if verbose:
        print(f"loaded {len(curves)} usable curves from {len(runs)} runs; dropped: {dropped}")
    return curves
