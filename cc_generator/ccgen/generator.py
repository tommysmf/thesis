"""Build semi-synthetic cases from real heating curves and write them out.

Output is split in two folders so nothing hidden leaks into training by accident:

  observed/   what a prescriptive method may use
    event_log.csv        real setup events + synthetic "Start spinning" + "Candy finished" (with weight)
    sensor_stream.csv    sensor readings up to the start (head temperature on the waiting path)
    decision_points.csv  one row per case x decision point up to the start: state + whether it started there
    cases.csv            one row per case: attributes, start moment, observed outcome y, split
  truth/      the answer key, for scoring only
    answer_key.csv       one row per case x decision point (ALL points): true start chance and the
                         outcome if spinning started there (expected and with the case's noise)
    case_truth.csv       per case: optimal temperature, best start moment, regret of the historical start
"""
import os
import json
import numpy as np
import pandas as pd

from .mechanisms import start_probability, historical_start, start_distribution, optimal_head, expected_outcome

SPIN_PLUS_MEASURE_S = 150.0   # time from start to the finished, weighed candy in the generated log (cosmetic)


def split_curves(curves, cfg):
    """Assign whole real curves to train or test, so a curve never appears on both sides."""
    rng = np.random.default_rng(cfg.seed)
    ids = np.array(sorted(c.curve_id for c in curves))
    rng.shuffle(ids)
    n_test = int(round(cfg.test_share * len(ids)))
    test = set(ids[:n_test].tolist())
    return {c.curve_id: ("test" if c.curve_id in test else "train") for c in curves}


def case_states(curve, cfg, stretch=1.0):
    """Decision grid and the sensor state at each point, following the waiting path."""
    t = np.arange(curve.t_ready, curve.t_end + 1e-9, cfg.grid_seconds)
    head = curve.waiting_head(t, cfg.after_start_slowdown, stretch)
    head_10s_ago = curve.waiting_head(np.maximum(t - 10.0, curve.x.min()), cfg.after_start_slowdown, stretch)
    return t, head, (head - head_10s_ago) / 10.0


def build_case(curve, rep, cfg, rng, split):
    stretch = 1.0 + (rng.uniform(-cfg.curve_stretch, cfg.curve_stretch) if cfg.curve_stretch > 0 else 0.0)
    t, head, slope = case_states(curve, cfg, stretch)
    h_opt = optimal_head(curve.wear, curve.hum_z, cfg)
    p = start_probability(head, t, cfg)
    k_start, followed_rule = historical_start(p, cfg, rng)
    ey = expected_outcome(head, t, h_opt, cfg)
    noise = rng.normal(0.0, cfg.noise_sd)
    return dict(case_id=f"{curve.curve_id}-{rep:03d}", curve=curve, rep=rep, split=split, stretch=stretch,
                t=t, head=head, slope=slope, h_opt=h_opt, p=p, k_start=k_start, followed_rule=followed_rule,
                ey=ey, noise=noise)


def generate(curves, cfg):
    rng = np.random.default_rng(cfg.seed + 1)
    splits = split_curves(curves, cfg)
    cases = [build_case(c, rep, cfg, rng, splits[c.curve_id])
             for c in curves for rep in range(cfg.resamples_per_curve)]
    return cases, tables(cases, cfg)


def tables(cases, cfg):
    case_rows, dp_rows, key_rows, truth_rows, log_rows, sensor_rows = [], [], [], [], [], []
    for cs in cases:
        c, k, t, head = cs["curve"], cs["k_start"], cs["t"], cs["head"]
        base = c.machine_on + pd.Timedelta(days=cs["rep"])       # each resample gets its own day
        y = float(cs["ey"][k] + cs["noise"])
        case_rows.append(dict(case_id=cs["case_id"], curve_id=c.curve_id, split=cs["split"], batch=c.batch,
                              wear=c.wear, env_temp=c.env_temp, env_hum=c.env_hum, t_ready=c.t_ready,
                              n_points=len(t), start_point=k, t_start=t[k], head_start=head[k], y=y))
        # decision points up to (and including) the start
        for j in range(k + 1):
            dp_rows.append(dict(case_id=cs["case_id"], point=j, t=t[j], head=head[j], head_slope=cs["slope"][j],
                                env_temp=c.env_temp, env_hum=c.env_hum, wear=c.wear, started=int(j == k)))
        # answer key: every point
        dist = start_distribution(cs["p"], cfg.delta)
        best = int(np.argmax(cs["ey"]))
        for j in range(len(t)):
            key_rows.append(dict(case_id=cs["case_id"], point=j, t=t[j], head=head[j], p_start_hazard=cs["p"][j],
                                 p_start_here=dist[j], expected_y=cs["ey"][j], y_if_start=cs["ey"][j] + cs["noise"],
                                 is_best=int(j == best)))
        truth_rows.append(dict(case_id=cs["case_id"], h_opt=cs["h_opt"], best_point=best, t_best=t[best],
                               head_best=head[best], expected_y_best=cs["ey"][best],
                               expected_y_historical=cs["ey"][k], regret=cs["ey"][best] - cs["ey"][k],
                               expected_y_policy_average=float(np.dot(dist, cs["ey"])), noise=cs["noise"],
                               followed_rule=int(cs["followed_rule"]),
                               stretch=cs["stretch"]))
        # event log
        for _, e in c.setup_events.iterrows():
            log_rows.append(dict(case_id=cs["case_id"], t=e.t, timestamp=base + pd.Timedelta(seconds=e.t),
                                 activity=e.activity, weight=np.nan))
        log_rows.append(dict(case_id=cs["case_id"], t=t[k], timestamp=base + pd.Timedelta(seconds=t[k]),
                             activity="Start spinning", weight=np.nan))
        t_fin = t[k] + SPIN_PLUS_MEASURE_S
        log_rows.append(dict(case_id=cs["case_id"], t=t_fin, timestamp=base + pd.Timedelta(seconds=t_fin),
                             activity="Candy finished", weight=y))
        # sensor stream up to the start, at the real reading times, head on the waiting path
        xs = c.x[(c.x >= c.setup_events.t.min() if len(c.setup_events) else c.x >= -60) & (c.x <= t[k])]
        hx = c.waiting_head(xs, cfg.after_start_slowdown, cs["stretch"])
        for xi, hi in zip(xs, hx):
            sensor_rows.append(dict(case_id=cs["case_id"], t=xi, timestamp=base + pd.Timedelta(seconds=float(xi)),
                                    ir_head=hi, env_temp=c.env_temp, env_hum=c.env_hum))
    return dict(cases=pd.DataFrame(case_rows), decision_points=pd.DataFrame(dp_rows),
                answer_key=pd.DataFrame(key_rows), case_truth=pd.DataFrame(truth_rows),
                event_log=pd.DataFrame(log_rows).sort_values(["case_id", "t"]),
                sensor_stream=pd.DataFrame(sensor_rows))


def write(tabs, cfg, out_dir):
    obs, tru = os.path.join(out_dir, "observed"), os.path.join(out_dir, "truth")
    os.makedirs(obs, exist_ok=True)
    os.makedirs(tru, exist_ok=True)
    for name in ["event_log", "sensor_stream", "decision_points", "cases"]:
        tabs[name].to_csv(os.path.join(obs, f"{name}.csv"), index=False)
    for name in ["answer_key", "case_truth"]:
        tabs[name].to_csv(os.path.join(tru, f"{name}.csv"), index=False)
    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump(cfg.to_dict(), f, indent=2)
