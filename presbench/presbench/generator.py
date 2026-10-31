"""Turn real cases into a semi-synthetic benchmark: the core of presbench.

For every real case (resampled `resamples_per_case` times) the generator:
  1. takes the decision points from the adapter's RealCase (the real signal readings in the window);
  2. draws the case's random parts: a hidden factor u ~ N(0, 1), the policy arm, the outcome noise;
  3. picks the historical decision point: with probability delta the adapter's historical policy,
     otherwise a uniformly random decision point;
  4. computes the propensity of every decision point (exact, from observable information only);
  5. computes the expected outcome of EVERY decision point with the adapter's outcome model, and the
     same averaged over u ("observable" expectation, if the outcome uses u);
  6. writes what a method may see (observed/) apart from the answer key (truth/).

Output files (column names use the adapter's signal_name and outcome_name):
  observed/event_log.csv        real events before the window + the intervention + the outcome event
  observed/sensor_stream.csv    the signal (and extra channels) at the real reading times, up to the intervention
  observed/decision_points.csv  one row per decision point up to the intervention (convenience view)
  observed/cases.csv            per case: group, attributes, split, chosen decision point, measured outcome, KPI y
  truth/answer_key.csv          per case x decision point (all): signal, propensity, expected outcome and KPI
  truth/case_truth.csv          per case: policy arm and setting, hidden factor, outcome info, best point, regret
"""
import os
import json
import numpy as np
import pandas as pd

# nodes and weights to average over the hidden factor u ~ N(0, 1)
U_NODES, U_WEIGHTS = np.polynomial.hermite_e.hermegauss(9)
U_WEIGHTS = U_WEIGHTS / U_WEIGHTS.sum()


def _order(case_id):
    return (len(str(case_id)), str(case_id))


def split_cases(cases, settings):
    """Assign whole real cases to train or test, so a real case never appears on both sides."""
    rng = np.random.default_rng(settings.seed)
    ids = np.array(sorted((c.case_id for c in cases), key=_order), dtype=object)
    rng.shuffle(ids)
    n_test = int(round(settings.test_share * len(ids)))
    test = set(ids[:n_test].tolist())
    return {c.case_id: ("test" if c.case_id in test else "train") for c in cases}


def draw_case(settings, rng):
    """The random parts of one generated case that do not depend on the policy (fixed order: u, arm, noise)."""
    return dict(hidden=float(rng.normal()), u_arm=rng.random(), noise=float(rng.normal(0.0, settings.noise_sd)))


def build_case(case, rep, settings, rng, split, policy, outcome):
    """One generated case: the historical decision, propensities and the outcome of every decision point."""
    d = draw_case(settings, rng)
    dp = case.decision_points()
    n = len(dp)
    if d["u_arm"] < settings.delta:
        arm, setting, k = policy.sample(case, dp, d["hidden"], rng)
    else:
        arm, setting, k = "random", np.nan, int(rng.integers(n))
    pi = settings.delta * policy.distribution(case, dp) + (1 - settings.delta) / n
    measure, kpi = outcome.expected(case, dp, d["hidden"])
    if outcome.uses_hidden:     # expected KPI knowing only what a method can see
        kpi_obs = sum(w * outcome.expected(case, dp, u)[1] for u, w in zip(U_NODES, U_WEIGHTS))
    else:
        kpi_obs = kpi
    return dict(case_id=f"{case.case_id}-{rep:03d}", case=case, rep=rep, split=split, dp=dp, pi=pi, arm=arm,
                setting=setting, hidden=d["hidden"], k=k, measure=measure, kpi=kpi, kpi_obs=kpi_obs,
                truth_info=outcome.truth_info(case, d["hidden"]), noise=d["noise"])


def generate(adapter, cases, settings):
    """Generate all cases. Returns (generated cases as dicts, tables as DataFrames).
    The policy is built from the cases passed in, so pass all usable cases."""
    rng = np.random.default_rng(settings.seed + 1)
    splits = split_cases(cases, settings)
    policy = adapter.policy(cases, settings.params)
    outcome = adapter.outcome(settings.params)
    generated = [build_case(c, rep, settings, rng, splits[c.case_id], policy, outcome)
                 for c in cases for rep in range(settings.resamples_per_case)]
    return generated, tables(adapter, generated)


def _locf(times, values, at):
    """Last observation carried forward at times `at` (the first value before the first reading)."""
    pos = np.searchsorted(times, at, side="right") - 1
    return np.asarray(values)[np.maximum(pos, 0)]


def tables(adapter, generated):
    sig, out = adapter.signal_name, adapter.outcome_name
    case_rows, dp_rows, key_rows, truth_rows, log_rows, sensor_rows = [], [], [], [], [], []
    for g in generated:
        c, k, dp = g["case"], g["k"], g["dp"]
        t = dp.t
        base = c.t0 + pd.Timedelta(days=g["rep"])            # each resample gets its own day
        measured = float(g["measure"][k] + g["noise"])
        y = float(g["kpi"][k] + g["noise"])
        case_rows.append(dict(case_id=g["case_id"], real_case_id=c.case_id, split=g["split"], group=c.group,
                              **c.attributes, t_open=c.t_open, start_point=k, t_start=t[k],
                              **{f"{sig}_at_start": dp.signal[k], out: measured, "y": y}))
        for j in range(k + 1):
            dp_rows.append({"case_id": g["case_id"], "point": j, "t": t[j], sig: dp.signal[j], "started": int(j == k)})
        best = int(np.argmax(g["kpi"]))
        best_obs = int(np.argmax(g["kpi_obs"]))
        for j in range(len(t)):
            key_rows.append({"case_id": g["case_id"], "point": j, "t": t[j], sig: dp.signal[j],
                             "p_start_here": g["pi"][j], f"expected_{out}": g["measure"][j],
                             "expected_y": g["kpi"][j], "expected_y_observable": g["kpi_obs"][j],
                             "y_if_start": g["kpi"][j] + g["noise"], "is_best": int(j == best)})
        truth_rows.append(dict(case_id=g["case_id"], arm=g["arm"], setting=g["setting"], hidden=g["hidden"],
                               **g["truth_info"], best_point=best, t_best=t[best], **{f"{sig}_best": dp.signal[best]},
                               expected_y_best=g["kpi"][best], expected_y_historical=g["kpi"][k],
                               regret=g["kpi"][best] - g["kpi"][k], best_point_observable=best_obs,
                               expected_y_best_observable=g["kpi"][best_obs],
                               expected_y_policy_average=float(np.dot(g["pi"], g["kpi"])), noise=g["noise"]))
        for _, e in c.events.iterrows():
            log_rows.append({"case_id": g["case_id"], "t": e.t, "timestamp": base + pd.Timedelta(seconds=e.t),
                             "activity": e.activity, out: np.nan})
        log_rows.append({"case_id": g["case_id"], "t": t[k], "timestamp": base + pd.Timedelta(seconds=t[k]),
                         "activity": adapter.intervention_activity, out: np.nan})
        t_fin = t[k] + adapter.outcome_delay
        log_rows.append({"case_id": g["case_id"], "t": t_fin, "timestamp": base + pd.Timedelta(seconds=t_fin),
                         "activity": adapter.outcome_activity, out: measured})
        # sensor stream: every signal reading from the first logged event (or t = 0) until the intervention
        first = c.events.t.min() if len(c.events) else -60.0
        m = (c.times >= min(first, 0.0)) & (c.times <= t[k])
        extra = {name: _locf(np.asarray(ct), cv, c.times[m]) for name, (ct, cv) in c.channels.items()}
        for i, (xi, si) in enumerate(zip(c.times[m], c.signal[m])):
            sensor_rows.append({"case_id": g["case_id"], "t": xi, "timestamp": base + pd.Timedelta(seconds=float(xi)),
                                sig: si, **{name: v[i] for name, v in extra.items()}})
    return dict(cases=pd.DataFrame(case_rows), decision_points=pd.DataFrame(dp_rows),
                answer_key=pd.DataFrame(key_rows), case_truth=pd.DataFrame(truth_rows),
                event_log=pd.DataFrame(log_rows).sort_values(["case_id", "t"]),
                sensor_stream=pd.DataFrame(sensor_rows))


def write(tables_, settings, adapter, out_dir):
    obs, tru = os.path.join(out_dir, "observed"), os.path.join(out_dir, "truth")
    os.makedirs(obs, exist_ok=True)
    os.makedirs(tru, exist_ok=True)
    for name in ["event_log", "sensor_stream", "decision_points", "cases"]:
        tables_[name].to_csv(os.path.join(obs, f"{name}.csv"), index=False)
    for name in ["answer_key", "case_truth"]:
        tables_[name].to_csv(os.path.join(tru, f"{name}.csv"), index=False)
    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump({"adapter": adapter.name, **settings.to_dict()}, f, indent=2)
