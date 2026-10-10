"""Build semi-synthetic cases from real heating curves and write them out.

Output is split in two folders so nothing hidden leaks into training by accident:

  observed/   what a prescriptive method may use
    event_log.csv        real setup events + synthetic "Start spinning" + "Candy finished" (with the weight)
    sensor_stream.csv    observed head readings (real times, irregular) up to the start
    decision_points.csv  convenience view: one row per case x decision point (= reading) up to the start,
                         with the observed reading and whether spinning started there
    cases.csv            one row per case: attributes, start moment, observed weight and KPI, split
  truth/      the answer key, for scoring only
    answer_key.csv       one row per case x decision point (ALL points): head reading, start chance given what
                         a method can see, and the outcome if spinning started there
    case_truth.csv       per case: which policy decided, its setting, optimal temperature, best moment, regret
"""
import os
import json
import numpy as np
import pandas as pd

from .mechanisms import (controller_point, fixed_wait_point, point_distribution, controller_distribution_hidden,
                         optimal_head, expected_weight, expected_kpi)

SPIN_PLUS_MEASURE_S = 150.0   # time from start to the finished, weighed candy in the generated log (cosmetic)
# nodes and weights to average over the unobserved factor u ~ N(0, 1)
_U, _UW = np.polynomial.hermite_e.hermegauss(9)
_UW = _UW / _UW.sum()


def split_curves(curves, cfg):
    """Assign whole real curves to train or test, so a curve never appears on both sides."""
    rng = np.random.default_rng(cfg.seed)
    ids = np.array(sorted(c.curve_id for c in curves))
    rng.shuffle(ids)
    n_test = int(round(cfg.test_share * len(ids)))
    test = set(ids[:n_test].tolist())
    return {c.curve_id: ("test" if c.curve_id in test else "train") for c in curves}


def policy_pools(curves, cfg):
    """For every curve: the real settings of comparable runs, the pool its historical setting is drawn from.

    Fixed waiting time (batches 0-14): real waits of runs in the same batch with the same cold/warm machine
    (a cold machine: the waits of all cold starts, about 105 s), the `pool_size` nearest in wear.
    Controller (batches 15-23): real start temperatures of runs in the same batch where the warm-up loop polled,
    the `pool_size` nearest in wear. Batch, machine temperature at "stick placed" and wear are all observable,
    so the propensity computed from the pool uses only what a method can see.
    """
    pools = {}
    for c in curves:
        if c.real_controller:
            cand = [o for o in curves if o.real_controller and o.loop_ran and o.batch == c.batch]
            value = lambda o: float(np.interp(o.t_real_start, o.x, o.head))
        elif c.cold:
            cand = [o for o in curves if not o.real_controller and o.cold]
            value = lambda o: o.real_wait
        else:
            cand = [o for o in curves if not o.real_controller and not o.cold and o.batch == c.batch]
            value = lambda o: o.real_wait
        cand = sorted(cand, key=lambda o: (abs(o.wear - c.wear), o.curve_id))[:cfg.pool_size]
        pools[c.curve_id] = [value(o) for o in cand]
    return pools


def case_states(curve):
    """Decision points (= real readings in the window) and the head reading at each."""
    x = curve.x
    idx = np.nonzero((x >= curve.t_ready) & (x <= curve.t_end))[0]
    return dict(idx=idx, t=x[idx], t_rel=x[idx] - curve.t_ready, head=curve.head[idx])


def draw_case(curve, cfg, rng):
    """The random parts of one case that do not depend on the policy."""
    return dict(hidden=float(rng.normal()), u_arm=rng.random(), noise=float(rng.normal(0.0, cfg.noise_sd)))


def historical_distribution(curve, st, pool, cfg):
    """Exact chance of each start point under the historical policy, given only observable information:
    the average over the comparable runs' settings (and over the hidden factor when it moves the threshold)."""
    n = len(st["t"])
    if curve.real_controller:
        if cfg.hidden_policy:
            return np.mean([controller_distribution_hidden(st["head"], thr, cfg.hidden_policy) for thr in pool], axis=0)
        return point_distribution([controller_point(st["head"], thr) for thr in pool], n)
    return point_distribution([fixed_wait_point(st["t_rel"], w) for w in pool], n)


def build_case(curve, rep, cfg, rng, split, pools):
    d = draw_case(curve, cfg, rng)
    st = case_states(curve)
    n = len(st["t"])
    pool = pools[curve.curve_id]
    if d["u_arm"] < cfg.delta:
        setting = float(rng.choice(pool))
        if curve.real_controller:
            arm, k = "controller", controller_point(st["head"], setting + cfg.hidden_policy * d["hidden"])
        else:
            arm, k = "fixed_wait", fixed_wait_point(st["t_rel"], setting)
    else:
        arm, setting, k = "random", np.nan, int(rng.integers(n))
    pi = cfg.delta * historical_distribution(curve, st, pool, cfg) + (1 - cfg.delta) / n
    h_opt = optimal_head(curve.wear, curve.hum_z, cfg, d["hidden"])
    ew = expected_weight(st["head"], h_opt, cfg)
    ey = expected_kpi(st["head"], st["t_rel"], h_opt, cfg)
    if cfg.hidden_effect:   # expected KPI knowing only what a method can see
        ey_obs = sum(wu * expected_kpi(st["head"], st["t_rel"], optimal_head(curve.wear, curve.hum_z, cfg, u), cfg)
                     for u, wu in zip(_U, _UW))
    else:
        ey_obs = ey
    return dict(case_id=f"{curve.curve_id}-{rep:03d}", curve=curve, rep=rep, split=split, st=st, pi=pi,
                arm=arm, setting=setting, hidden=d["hidden"], k_start=k, h_opt=h_opt, ew=ew, ey=ey, ey_obs=ey_obs,
                noise=d["noise"])


def generate(curves, cfg):
    rng = np.random.default_rng(cfg.seed + 1)
    splits = split_curves(curves, cfg)
    pools = policy_pools(curves, cfg)    # note: built from the curves passed in
    cases = [build_case(c, rep, cfg, rng, splits[c.curve_id], pools)
             for c in curves for rep in range(cfg.resamples_per_curve)]
    return cases, tables(cases, cfg)


def tables(cases, cfg):
    case_rows, dp_rows, key_rows, truth_rows, log_rows, sensor_rows = [], [], [], [], [], []
    for cs in cases:
        c, k, st = cs["curve"], cs["k_start"], cs["st"]
        t = st["t"]
        base = c.machine_on + pd.Timedelta(days=cs["rep"])       # each resample gets its own day
        weight = float(cs["ew"][k] + cs["noise"])
        y = float(cs["ey"][k] + cs["noise"])
        case_rows.append(dict(case_id=cs["case_id"], curve_id=c.curve_id, split=cs["split"], batch=c.batch,
                              wear=c.wear, env_temp=c.env_temp, env_hum=c.env_hum, t_ready=c.t_ready,
                              start_point=k, t_start=t[k], head_start=st["head"][k], weight=weight, y=y))
        for j in range(k + 1):
            dp_rows.append(dict(case_id=cs["case_id"], point=j, t=t[j], head=st["head"][j], started=int(j == k)))
        best = int(np.argmax(cs["ey"]))
        best_obs = int(np.argmax(cs["ey_obs"]))      # best moment knowing only what a method can see
        for j in range(len(t)):
            key_rows.append(dict(case_id=cs["case_id"], point=j, t=t[j], head=st["head"][j], p_start_here=cs["pi"][j],
                                 expected_weight=cs["ew"][j], expected_y=cs["ey"][j],
                                 expected_y_observable=cs["ey_obs"][j], y_if_start=cs["ey"][j] + cs["noise"],
                                 is_best=int(j == best)))
        truth_rows.append(dict(case_id=cs["case_id"], arm=cs["arm"], setting=cs["setting"], hidden=cs["hidden"],
                               h_opt=cs["h_opt"], best_point=best, t_best=t[best], head_best=st["head"][best],
                               expected_y_best=cs["ey"][best], expected_y_historical=cs["ey"][k],
                               regret=cs["ey"][best] - cs["ey"][k], best_point_observable=best_obs,
                               expected_y_best_observable=cs["ey"][best_obs],
                               expected_y_policy_average=float(np.dot(cs["pi"], cs["ey"])), noise=cs["noise"]))
        for _, e in c.setup_events.iterrows():
            log_rows.append(dict(case_id=cs["case_id"], t=e.t, timestamp=base + pd.Timedelta(seconds=e.t),
                                 activity=e.activity, weight=np.nan))
        log_rows.append(dict(case_id=cs["case_id"], t=t[k], timestamp=base + pd.Timedelta(seconds=t[k]),
                             activity="Start spinning", weight=np.nan))
        t_fin = t[k] + SPIN_PLUS_MEASURE_S
        log_rows.append(dict(case_id=cs["case_id"], t=t_fin, timestamp=base + pd.Timedelta(seconds=t_fin),
                             activity="Candy finished", weight=weight))
        # sensor stream: every observed reading from the setup until the start, at the real reading times
        first = c.setup_events.t.min() if len(c.setup_events) else -60.0
        m = (c.x >= min(first, 0.0)) & (c.x <= t[k])
        for xi, hi in zip(c.x[m], c.head[m]):
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
