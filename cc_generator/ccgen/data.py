"""Load the real cotton candy runs (output of prepare_cotton_candy.py) as heating curves.

Each usable run becomes a Curve: the real head-temperature readings (at their real, irregular times),
the real setup events, the case attributes, and what the real run did (when it really started
spinning, and whether a temperature controller or a fixed waiting time decided that).

How the real process starts spinning (checked on the data, see the specification):
  * batches 0-14: "Create Cotton Candy" first waits the configured `wait_time`, then spins for
    `cook_time` (the step lasts wait_time + cook_time + ~7 s). Spin start = create_calling + wait_time.
  * batches 15-23: the waiting time setting is ignored (the step lasts cook_time). A warm-up loop
    ("Run until CC Head is optimally warm") polls the head temperature BEFORE "Create Cotton Candy" and
    is skipped when the head is already warm; spinning starts at create_calling.
"""
from dataclasses import dataclass
import os
import numpy as np
import pandas as pd

TS = dict(utc=True, format="ISO8601", errors="coerce")
# real activities kept in the generated log (setup before spinning); the real "Set waiting/cooking time"
# events are left out on purpose: they reveal the REAL operator's decision
SETUP_ACTIVITIES = ["Set the Sugar Amount for Size", "Fill Machine with Sugar", "Turn the Machine On",
                    "Set the Stick Number", "Place the Wood Stick in Center"]
READY_ACTIVITY = "Place the Wood Stick in Center"   # spinning can start once the stick is placed
CONTROLLER_ACTIVITY = "Run until CC Head is optimally warm"
FIRST_CONTROLLER_BATCH = 15     # from this batch on, a temperature controller decides the start
PEAK_SMOOTH_S = 10.0     # s: smoothing used only to find the temperature peak that ends the window
COLD_HEAD = 40.0         # degC: a head below this when the stick is placed counts as a cold machine


@dataclass
class Curve:
    curve_id: int              # real run instance id
    batch: str
    machine_on: pd.Timestamp   # real absolute time of t = 0
    t_ready: float             # s: stick placed, first possible start
    t_real_start: float        # s: when the real run started spinning
    t_end: float               # s: last decision point (window end)
    real_controller: bool      # True if a temperature controller decided the real start (batches 15-23)
    loop_ran: bool             # True if the warm-up loop actually polled (its start temperature is a threshold)
    x: np.ndarray              # s since machine on: times of the raw head readings (irregular)
    head: np.ndarray           # degC: raw infrared head readings
    env_temp: float            # degC, ambient temperature (mean up to stick placed)
    env_hum: float             # %, ambient humidity (mean up to stick placed)
    wear: float                # iterations since maintenance
    setup_events: pd.DataFrame # columns activity, t (real setup before t_ready)

    @property
    def real_wait(self):
        """s from stick placed to the real spin start."""
        return self.t_real_start - self.t_ready

    @property
    def head_at_ready(self):
        return float(np.interp(self.t_ready, self.x, self.head))

    @property
    def cold(self):
        """A cold machine: the operators of batches 0-14 then waited about 105 s."""
        return self.head_at_ready < COLD_HEAD


def _smooth(x, v, width):
    """Centred moving average over a time window (works for irregular readings)."""
    out = np.empty_like(v)
    lo = np.searchsorted(x, x - width / 2)
    hi = np.searchsorted(x, x + width / 2, side="right")
    c = np.concatenate([[0.0], np.cumsum(v)])
    out[:] = (c[hi] - c[lo]) / (hi - lo)
    return out


def load_curves(processed_dir, min_window=20.0, max_window=120.0, verbose=True):
    runs = pd.read_csv(os.path.join(processed_dir, "runs.csv"))
    sensors = pd.read_csv(os.path.join(processed_dir, "sensors.csv"))
    events = pd.read_csv(os.path.join(processed_dir, "events.csv"))
    for c in ["machine_on_done", "create_calling", "create_done"]:
        runs[c] = pd.to_datetime(runs[c], **TS)
    sensors["ts"] = pd.to_datetime(sensors["ts"], **TS)
    events["time"] = pd.to_datetime(events["time"], **TS)
    controller_runs = set(events.loc[events.activity == CONTROLLER_ACTIVITY, "instance"])

    curves, dropped = [], {}
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
        # (later the real machine cools down) and at most max_window after the stick is placed
        lim = min(t_ready + max_window, t_real_end)
        m = (x >= t_ready) & (x <= lim)
        if m.sum() < 5:
            drop("heating window too short"); continue
        t_end = float(x[m][int(np.argmax(smooth[m]))])
        if t_end - t_ready < min_window:
            drop("heating window too short"); continue
        env = s[s.env_temp.notna() & (s.x <= t_ready)]
        if env.empty:
            env = s[s.env_temp.notna()].head(3)
        setup = ev[ev.activity.isin(SETUP_ACTIVITIES) & (ev.t >= -90) & (ev.t <= t_ready)]
        setup = setup.sort_values("t").drop_duplicates("activity", keep="last")[["activity", "t"]]
        curves.append(Curve(
            curve_id=int(run.instance), batch=run.batch, machine_on=t0, t_ready=t_ready,
            t_real_start=t_real_start, t_end=t_end, real_controller=controller,
            loop_ran=run.instance in controller_runs, x=x, head=head,
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
