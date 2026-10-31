"""Generic checks of a generated benchmark (used by validate.py).

  baselines()      value of simple policies on the test cases, against the oracle: is there something to gain,
                   and how much of it does a simple sensor rule already get?
  naive_vs_truth() does a naive comparison in the observed log get the effect of waiting wrong (confounding)?
  run()            the same over several seeds, for any combination of knobs
  report()         the full validation report: adapter realism checks, baselines, knob sweeps, scenarios
All policy values use the EXPECTED KPI from the answer key (no noise), on the TEST cases.
"""
import numpy as np

from .config import make_settings
from .generator import generate


def pct(s):
    return tuple(float(v) for v in np.percentile(s, [10, 50, 90]).round(1))


def ms(values, digits=2):
    v = np.asarray(values, dtype=float)
    return f"{v.mean():.{digits}f} +- {v.std():.{digits}f}" if len(v) > 1 else f"{v.mean():.{digits}f}"


def contrast_windows(adapter, generated):
    """Early and late waiting windows (s after t_open) for the naive check: the adapter's choice, or else
    the first 5% vs 10-40% of the median window length."""
    if getattr(adapter, "naive_contrast", None):
        return adapter.naive_contrast
    length = np.median([g["dp"].t_rel[-1] for g in generated])
    return (0.0, 0.05 * length), (0.10 * length, 0.40 * length)


def naive_vs_truth(tables, early, late):
    """Effect of waiting `late` instead of `early` (s after t_open): truth from the answer key (all cases) vs a
    naive comparison of the observed KPI of cases that happened to intervene then."""
    key, cases = tables["answer_key"], tables["cases"]
    key = key.merge(cases[["case_id", "t_open"]], on="case_id")
    key["delay"] = key.t - key.t_open
    pick = lambda lo, hi: key[(key.delay >= lo) & (key.delay <= hi)].groupby("case_id").expected_y.mean()
    truth = (pick(*late) - pick(*early)).mean()
    cases = cases.assign(delay=cases.t_start - cases.t_open)
    e = cases[(cases.delay >= early[0]) & (cases.delay <= early[1])].y
    l = cases[(cases.delay >= late[0]) & (cases.delay <= late[1])].y
    if len(e) == 0 or len(l) == 0:     # no historical decisions in a window: the check is undefined
        return truth, float("nan")
    return truth, l.mean() - e.mean()


def trailing_mean(x, v, width=10.0):
    """Mean of the readings in the last `width` seconds (a method could compute this online)."""
    lo = np.searchsorted(x, x - width)
    c = np.concatenate([[0.0], np.cumsum(v)])
    idx = np.arange(len(v)) + 1
    return (c[idx] - c[lo]) / (idx - lo)


def _first_at_least(values, threshold):
    hit = np.nonzero(values >= threshold)[0]
    return hit[0] if len(hit) else len(values) - 1


def baselines(generated, direction=1):
    """Policy values on the test cases (expected KPI, mean over cases). Thresholds act on what a method can see:
    the current signal reading, or the mean of the readings in the last 10 s; direction -1 = falling signal."""
    test = [g for g in generated if g["split"] == "test"]
    sig = np.concatenate([g["dp"].signal for g in test])
    thresholds = np.linspace(np.percentile(sig, 1), np.percentile(sig, 99), 60)
    delays = np.arange(0, max(g["dp"].t_rel[-1] for g in test) + 10, 10)
    v = {"historical policy": [], "oracle": [], "observable oracle": []}
    by_delay = {d: [] for d in delays}
    by_raw = {T: [] for T in thresholds}
    by_avg = {T: [] for T in thresholds}
    for g in test:
        dp, ey = g["dp"], g["kpi"]
        avg = trailing_mean(g["case"].times, g["case"].signal)[dp.idx]
        v["historical policy"].append(ey[g["k"]])
        v["oracle"].append(ey.max())
        v["observable oracle"].append(ey[int(np.argmax(g["kpi_obs"]))])
        for d in delays:
            by_delay[d].append(ey[_first_at_least(dp.t_rel, d)])
        for T in thresholds:
            by_raw[T].append(ey[_first_at_least(direction * dp.signal, direction * T)])
            by_avg[T].append(ey[_first_at_least(direction * avg, direction * T)])
    res = {k: float(np.mean(x)) for k, x in v.items()}
    res["best fixed delay"] = max(np.mean(x) for x in by_delay.values())
    res["best threshold, current reading"] = max(np.mean(x) for x in by_raw.values())
    res["best threshold, 10 s mean"] = max(np.mean(x) for x in by_avg.values())
    res["best is the first point (share)"] = float(np.mean([np.argmax(g["kpi"]) == 0 for g in test]))
    return res


def run(adapter, cases, seeds, resamples, scenario="realistic", **knobs):
    """Baselines and naive error for one configuration, over several seeds: dict of lists."""
    out = []
    for s in seeds:
        settings = make_settings(adapter, scenario, **knobs, seed=s, resamples_per_case=resamples)
        generated, tables = generate(adapter, cases, settings)
        b = baselines(generated, getattr(adapter, "signal_direction", 1))
        early, late = contrast_windows(adapter, generated)
        tr, nv = naive_vs_truth(tables, early, late)
        b["naive error"] = nv - tr
        out.append(b)
    return {k: [o[k] for o in out] for k in out[0]}


def report(adapter, cases, quick=False):
    """The full validation report as markdown lines."""
    seeds = [0] if quick else [0, 1, 2]
    resamples = 5 if quick else 10
    settings = make_settings(adapter, resamples_per_case=5 if quick else 20)
    generated, tables = generate(adapter, cases, settings)
    early, late = contrast_windows(adapter, generated)
    out = ["# Validation report", "", f"Adapter: `{adapter.name}`. Settings: `{settings.to_dict()}`", "",
           f"{len(tables['cases'])} cases from {len(cases)} real cases; decision points per case "
           f"{pct(tables['answer_key'].groupby('case_id').size())} (p10 / median / p90).", ""]
    rows = adapter.realism(cases, generated, tables)
    if rows:
        out += ["## 1. Realism (generated vs real, p10 / median / p90)", "", "| Quantity | Generated | Real |",
                "|---|---|---|"] + [f"| {n} | {g} | {r} |" for n, g, r in rows]
    out += adapter.realism_notes(cases, generated, tables)

    main = run(adapter, cases, seeds, resamples)
    out += ["", f"## 2. Baselines and confounding (defaults; mean +- sd over seeds {seeds})", "",
            "| Quantity | Value |", "|---|---|"]
    out += [f"| {k} | {ms(main[k])} |" for k in ["historical policy", "best fixed delay",
                                                  "best threshold, current reading", "best threshold, 10 s mean",
                                                  "oracle", "best is the first point (share)", "naive error"]]
    out += ["", f"Naive error = (naive estimate - truth) of the effect of intervening {late[0]:g}-{late[1]:g} s "
                f"instead of {early[0]:g}-{early[1]:g} s after the window opens."]
    if any(np.isnan(main["naive error"])):
        out += ["", "**The naive check is undefined (nan):** no historical decisions fall in one of the two windows. "
                    "Set the adapter's `naive_contrast` to windows where decisions do happen."]
    if quick:
        return out

    head = "| historical | best threshold, current reading | best threshold, 10 s mean | oracle | naive error |"
    out += ["", "## 3. Knobs"]
    for knob, values in adapter.sweeps:
        out += ["", f"`{knob}`:", "", f"| {knob} {head}", "|---" * 6 + "|"]
        for val in values:
            r = run(adapter, cases, seeds, resamples, **{knob: val})
            out.append(f"| {val} | {ms(r['historical policy'])} | {ms(r['best threshold, current reading'])} | "
                       f"{ms(r['best threshold, 10 s mean'])} | {ms(r['oracle'])} | {ms(r['naive error'])} |")
    out += ["", "## 4. Scenarios", "", "| scenario | historical | best threshold, current reading | "
            "best threshold, 10 s mean | observable oracle | oracle | naive error |", "|---" * 7 + "|"]
    for name in adapter.scenarios:
        r = run(adapter, cases, seeds, resamples, scenario=name)
        out.append(f"| {name} | {ms(r['historical policy'])} | {ms(r['best threshold, current reading'])} | "
                   f"{ms(r['best threshold, 10 s mean'])} | {ms(r['observable oracle'])} | {ms(r['oracle'])} | "
                   f"{ms(r['naive error'])} |")
    return out
