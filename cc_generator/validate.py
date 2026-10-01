"""Validation checks and baseline policies for the cotton candy generator.

    python validate.py --processed <path to cotton-candy/processed>  [--quick]

Prints the checks from the specification and writes validation_report.md next to this script.
All policy values use the EXPECTED outcome from the answer key (no noise), on the TEST curves.
"""
import argparse
import os
import numpy as np
import pandas as pd

from ccgen import Config, load_curves, generate
from ccgen.mechanisms import expected_outcome, optimal_head
from ccgen.generator import case_states

HERE = os.path.dirname(os.path.abspath(__file__))
REAL = dict(t_start=(19.0, 22.3, 38.9), head_start=(50.7, 58.1, 70.0), weight=(7.1, 8.6, 9.7))  # p10, median, p90


def pct(s):
    return tuple(float(v) for v in np.percentile(s, [10, 50, 90]).round(1))


def realism(tabs):
    c = tabs["cases"]
    rows = []
    for name, col in [("start time (s after machine on)", "t_start"), ("start head temperature (C)", "head_start"),
                      ("observed outcome (g)", "y")]:
        key = {"t_start": "t_start", "head_start": "head_start", "y": "weight"}[col]
        rows.append((name, pct(c[col]), REAL[key]))
    return rows


def naive_vs_truth(tabs, early=(0, 4), late=(10, 40)):
    """Value of 'start right at ready' vs 'start 10-40 s after ready'.
    Truth from the answer key (all cases); naive = compare observed y of cases that happened to start then."""
    key, cases = tabs["answer_key"], tabs["cases"]
    key = key.merge(cases[["case_id", "t_ready"]], on="case_id")
    key["delay"] = key.t - key.t_ready
    pick = lambda lo, hi: key[(key.delay >= lo) & (key.delay <= hi)].groupby("case_id").expected_y.mean()
    truth = (pick(*late) - pick(*early)).mean()
    cases = cases.assign(delay=cases.t_start - cases.t_ready)
    e = cases[(cases.delay >= early[0]) & (cases.delay <= early[1])].y
    l = cases[(cases.delay >= late[0]) & (cases.delay <= late[1])].y
    return truth, l.mean() - e.mean(), len(e), len(l)


def baselines(curves, tabs, cfg):
    """Policy values on the test curves (expected outcome, averaged over cases)."""
    test_ids = set(tabs["cases"].query("split == 'test'").curve_id)
    res = {}
    delays = np.arange(0, 121, 10)
    thresholds = np.arange(50, 81, 2)
    per = {"start at ready": [], "oracle (best moment per case)": []}
    per_delay = {d: [] for d in delays}
    per_thr = {T: [] for T in thresholds}
    for c in curves:
        if c.curve_id not in test_ids:
            continue
        t, head, _ = case_states(c, cfg)
        ey = expected_outcome(head, t, optimal_head(c.wear, c.hum_z, cfg), cfg)
        per["start at ready"].append(ey[0])
        per["oracle (best moment per case)"].append(ey.max())
        for d in delays:
            per_delay[d].append(ey[min(np.searchsorted(t, t[0] + d), len(t) - 1)])
        for T in thresholds:
            hit = np.nonzero(head >= T)[0]
            per_thr[T].append(ey[hit[0]] if len(hit) else ey[-1])
    truth = tabs["case_truth"].merge(tabs["cases"][["case_id", "split"]], on="case_id").query("split == 'test'")
    res["start at ready"] = np.mean(per["start at ready"])
    res["historical policy"] = truth.expected_y_historical.mean()
    best_d = max(delays, key=lambda d: np.mean(per_delay[d]))
    res[f"best fixed delay ({best_d} s after ready)"] = np.mean(per_delay[best_d])
    best_T = max(thresholds, key=lambda T: np.mean(per_thr[T]))
    res[f"best fixed threshold (start at {best_T} C)"] = np.mean(per_thr[best_T])
    res["oracle (best moment per case)"] = np.mean(per["oracle (best moment per case)"])
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--processed", required=True)
    ap.add_argument("--quick", action="store_true", help="fewer resamples and no knob sweeps")
    args = ap.parse_args()
    curves = load_curves(args.processed)
    cfg = Config(resamples_per_curve=5 if args.quick else 20)
    _, tabs = generate(curves, cfg)
    out = ["# Validation report", "", f"Config: `{cfg.to_dict()}`", ""]

    out += ["## 1. Realism (generated vs real, p10 / median / p90)", "", "| Quantity | Generated | Real |", "|---|---|---|"]
    for name, g, r in realism(tabs):
        out.append(f"| {name} | {g} | {r} |")

    truth, naive, ne, nl = naive_vs_truth(tabs)
    out += ["", "## 2. Confounding: waiting 10-40 s vs starting right away", "",
            f"True effect {truth:+.2f} g; naive comparison of observed cases {naive:+.2f} g "
            f"({ne} early starters vs {nl} late starters)."]

    out += ["", "## 3. Baseline policies (test curves, expected outcome in g)", "", "| Policy | Value |", "|---|---|"]
    for k, v in baselines(curves, tabs, cfg).items():
        out.append(f"| {k} | {v:.2f} |")

    if not args.quick:
        out += ["", "## 4. Knobs", "", "Confounding share delta (SimBank-style; true vs naive effect of waiting 10-40 s):", "",
                "| delta | true | naive | naive error | late starters |", "|---|---|---|---|---|"]
        for d in [0.0, 0.5, 0.75, 0.95, 1.0]:
            _, td = generate(curves, Config(delta=d, resamples_per_curve=40))
            tr, nv, _, nl = naive_vs_truth(td)
            out.append(f"| {d} | {tr:+.2f} | {nv:+.2f} | {nv - tr:+.2f} | {nl} |")
        out += ["", "Temperature dependence beta of the rule (not monotone in the naive error; see README):", "",
                "| beta | true | naive | naive error | late starters |", "|---|---|---|---|---|"]
        for b in [0.0, 0.15, 0.3, 0.6]:
            _, tb = generate(curves, Config(beta=b, resamples_per_curve=40))
            tr, nv, _, nl = naive_vs_truth(tb)
            out.append(f"| {b} | {tr:+.2f} | {nv:+.2f} | {nv - tr:+.2f} | {nl} |")
        out += ["", "Heterogeneity of the optimal temperature (a_wear, b_humidity scaled together):", "",
                "| scale | historical | best fixed threshold | oracle | oracle - threshold |", "|---|---|---|---|---|"]
        for f in [0.0, 0.5, 1.0, 1.5]:
            c3 = Config(a_wear=8.0 * f, b_humidity=-4.0 * f, resamples_per_curve=5)
            _, t3 = generate(curves, c3)
            b3 = baselines(curves, t3, c3)
            thr = [v for k, v in b3.items() if k.startswith("best fixed threshold")][0]
            orc = b3["oracle (best moment per case)"]
            out.append(f"| {f} | {b3['historical policy']:.2f} | {thr:.2f} | {orc:.2f} | {orc - thr:.2f} |")
        out += ["", "Heating correction after the real start (sensitivity of the conclusions):", "",
                "| slowdown | historical | oracle | gap |", "|---|---|---|---|"]
        for s in [0.7, 0.8, 0.9, 1.0]:
            c2 = Config(after_start_slowdown=s, resamples_per_curve=5)
            _, t2 = generate(curves, c2)
            b2 = baselines(curves, t2, c2)
            out.append(f"| {s} | {b2['historical policy']:.2f} | {b2['oracle (best moment per case)']:.2f} | "
                       f"{b2['oracle (best moment per case)'] - b2['historical policy']:.2f} |")

    report = "\n".join(out)
    print(report)
    with open(os.path.join(HERE, "validation_report.md"), "w") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    main()
