"""Checks of a generated two-stage benchmark (used by validate.py for TwoStageAdapter adapters).

  baselines()       policy values on the test cases (expected KPI from the answer key):
                      historical            both decisions by the historical policy
                      best second after historical first   only the second decision chosen well
                      greedy                the first decision chosen as if the historical policy then decides
                                            the second, followed by the best second decision
                      best fixed delays     wait d1 after t_open, then d2 after the first intervention
                      best thresholds       first reading >= T1, then first reading >= T2 at least m s later
                      oracle                the best pair (and the observable oracle if the outcome uses u)
  naive_vs_truth()  does a naive comparison in the observed log get the effect of a longer second phase wrong?
  run(), report()   the same over seeds, knob sweeps and scenarios
"""
import numpy as np

from .config import make_settings
from .twostage import generate, best_path
from .validation import ms, pct

MIN_GAPS = [0.0, 10.0, 20.0, 30.0, 45.0]      # s: minimum second phase for the threshold rule


def _first(cond):
    hit = np.nonzero(cond)[0]
    return int(hit[0]) if len(hit) else len(cond) - 1


def baselines(generated, direction=1):
    test = [g for g in generated if g["split"] == "test"]
    v = {k: [] for k in ["historical", "best second after historical first", "greedy", "oracle",
                         "observable oracle"]}
    for g in test:
        c, kpi = g["cache"], g["kpi"]
        v["historical"].append(kpi[g["k1"]][g["k2"]])
        v["best second after historical first"].append(float(np.max(kpi[g["k1"]])))
        j = int(np.argmax([np.dot(c.dist2[i], kpi[i]) for i in range(len(c.dp1))]))
        v["greedy"].append(float(np.max(kpi[j])))
        v["oracle"].append(best_path(kpi)[2])
        o1, o2, _ = best_path(g["kpi_obs"])
        v["observable oracle"].append(kpi[o1][o2])
    res = {k: float(np.mean(x)) for k, x in v.items()}

    # fixed delays: d1 after t_open, then d2 after the first intervention
    d1s = np.arange(0, max(g["cache"].dp1.t_rel[-1] for g in test) + 10, 10.0)
    gaps = [g["cache"].dp2[0].t - g["cache"].dp1.t[0] for g in test]
    d2s = np.arange(0, max(x[-1] for x in gaps) + 5, 5.0)
    tot = np.zeros((len(d1s), len(d2s)))
    for g in test:
        c = g["cache"]
        for a, d1 in enumerate(d1s):
            k1 = _first(c.dp1.t_rel >= d1)
            gap = c.dp2[k1].t - c.dp1.t[k1]
            tot[a] += g["kpi"][k1][[_first(gap >= d2) for d2 in d2s]]
    res["best fixed delays"] = float(tot.max() / len(test))
    a, b = np.unravel_index(np.argmax(tot), tot.shape)
    res["best fixed delays: d1, d2 (s)"] = (float(d1s[a]), float(d2s[b]))

    # thresholds on the signal at each stage (direction -1: reached from above)
    sig1 = np.concatenate([g["cache"].dp1.signal for g in test])
    sig2 = np.concatenate([d.signal for g in test for d in g["cache"].dp2[::5]])
    T1s = np.linspace(np.percentile(sig1, 1), np.percentile(sig1, 99), 30)
    T2s = np.linspace(np.percentile(sig2, 1), np.percentile(sig2, 99), 30)
    tot = np.zeros((len(T1s), len(T2s), len(MIN_GAPS)))
    for g in test:
        c = g["cache"]
        for a, T1 in enumerate(T1s):
            k1 = _first(direction * c.dp1.signal >= direction * T1)
            dp2 = c.dp2[k1]
            gap = dp2.t - c.dp1.t[k1]
            hit = direction * dp2.signal[:, None] >= direction * T2s[None, :]
            for m, mg in enumerate(MIN_GAPS):
                ok = hit & (gap >= mg)[:, None]
                k2 = np.where(ok.any(axis=0), ok.argmax(axis=0), len(dp2) - 1)
                tot[a, :, m] += g["kpi"][k1][k2]
    res["best thresholds"] = float(tot.max() / len(test))
    a, b, m = np.unravel_index(np.argmax(tot), tot.shape)
    res["best thresholds: T1, T2, min gap"] = (round(float(T1s[a]), 1), round(float(T2s[b]), 1), MIN_GAPS[m])
    return res


def naive_vs_truth(generated, tables, early, late):
    """Effect of a second phase of `late` instead of `early` (s after the first intervention), at the historical
    first decision: truth from the answer key vs a naive comparison of the observed KPI."""
    eff = []
    for g in generated:
        c = g["cache"]
        dp2, kpi = c.dp2[g["k1"]], g["kpi"][g["k1"]]
        gap = dp2.t - c.dp1.t[g["k1"]]
        e, l = (gap >= early[0]) & (gap <= early[1]), (gap >= late[0]) & (gap <= late[1])
        if e.any() and l.any():
            eff.append(kpi[l].mean() - kpi[e].mean())
    cs = tables["cases"].assign(gap=lambda d: d.t_second - d.t_first)
    ye = cs[(cs.gap >= early[0]) & (cs.gap <= early[1])].y
    yl = cs[(cs.gap >= late[0]) & (cs.gap <= late[1])].y
    truth = float(np.mean(eff)) if eff else float("nan")
    if len(ye) == 0 or len(yl) == 0:
        return truth, float("nan")
    return truth, float(yl.mean() - ye.mean())


def contrast_windows(adapter, generated):
    if getattr(adapter, "naive_contrast2", None):
        return adapter.naive_contrast2
    gaps = np.concatenate([g["cache"].dp2[g["k1"]].t[[0, -1]] - g["cache"].dp1.t[g["k1"]] for g in generated])
    lo, hi = np.percentile(gaps, [5, 95])
    return (lo, lo + 0.25 * (hi - lo)), (lo + 0.5 * (hi - lo), hi)


KEYS = ["historical", "best second after historical first", "greedy", "best fixed delays", "best thresholds",
        "observable oracle", "oracle", "naive error (second stage)"]


def run(adapter, cases, seeds, scenario="realistic", **knobs):
    out = []
    for s in seeds:
        settings = make_settings(adapter, scenario, **knobs, seed=s)
        generated, tables = generate(adapter, cases, settings)
        b = baselines(generated, getattr(adapter, "signal_direction", 1))
        early, late = contrast_windows(adapter, generated)
        tr, nv = naive_vs_truth(generated, tables, early, late)
        b["naive error (second stage)"] = nv - tr
        out.append(b)
    return {k: [o[k] for o in out] for k in out[0]}


def report(adapter, cases, quick=False):
    seeds = [0] if quick else [0, 1, 2]
    settings = make_settings(adapter)
    generated, tables = generate(adapter, cases, settings)
    early, late = contrast_windows(adapter, generated)
    s1, s2 = adapter.stage_names
    paths = tables["answer_key"].groupby("case_id").size()
    out = ["# Validation report (two linked decisions)", "",
           f"Adapter: `{adapter.name}` ({s1}, then {s2}). Settings: `{settings.to_dict()}`", "",
           f"{len(tables['cases'])} cases from {len(cases)} real cases; ({s1}, {s2}) paths per case "
           f"{pct(paths)} (p10 / median / p90).", ""]
    rows = adapter.realism(cases, generated, tables)
    if rows:
        out += ["## 1. Realism (generated historical cases vs real, p10 / median / p90)", "",
                "| Quantity | Generated | Real |", "|---|---|---|"] + [f"| {n} | {g} | {r} |" for n, g, r in rows]
    out += adapter.realism_notes(cases, generated, tables)

    main = run(adapter, cases, seeds)
    out += ["", f"## 2. Policies (test cases, expected KPI; mean +- sd over seeds {seeds})", "",
            "| Policy | Value |", "|---|---|"]
    out += [f"| {k} | {ms(main[k])} |" for k in KEYS]
    out += ["", f"Best fixed delays (seed {seeds[0]}): wait {main['best fixed delays: d1, d2 (s)'][0][0]:g} s, "
                f"then {s2} after {main['best fixed delays: d1, d2 (s)'][0][1]:g} s. Best thresholds: {s1} at "
                f"{main['best thresholds: T1, T2, min gap'][0][0]}, {s2} at "
                f"{main['best thresholds: T1, T2, min gap'][0][1]} after at least "
                f"{main['best thresholds: T1, T2, min gap'][0][2]:g} s.", "",
            f"Greedy = the {s1} chosen as if the historical policy then decides the {s2}, followed by the best "
            f"{s2}. Greedy vs oracle = what deciding both together is worth.", "",
            f"Naive error = (naive estimate - truth) of the effect of a {late[0]:g}-{late[1]:g} s instead of a "
            f"{early[0]:g}-{early[1]:g} s phase between the two decisions, at the historical {s1}."]
    if quick:
        return out
    head = "| historical | greedy | best thresholds | oracle | naive error (second stage) |"
    sweep_keys = ["historical", "greedy", "best thresholds", "oracle", "naive error (second stage)"]
    if adapter.sweeps:
        out += ["", "## 3. Knobs"]
    for knob, values in adapter.sweeps:
        out += ["", f"`{knob}`:", "", f"| {knob} {head}", "|---" * 6 + "|"]
        for val in values:
            r = run(adapter, cases, seeds, **{knob: val})
            out.append(f"| {val} | " + " | ".join(ms(r[k]) for k in sweep_keys) + " |")
    out += ["", "## 4. Scenarios", "", "| scenario " + head.replace("| oracle", "| observable oracle | oracle"),
            "|---" * 7 + "|"]
    for name in adapter.scenarios:
        r = run(adapter, cases, seeds, scenario=name)
        keys = ["historical", "greedy", "best thresholds", "observable oracle", "oracle", "naive error (second stage)"]
        out.append(f"| {name} | " + " | ".join(ms(r[k]) for k in keys) + " |")
    return out
