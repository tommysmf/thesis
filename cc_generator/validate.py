"""Validation checks and baseline policies for the cotton candy generator.

    python validate.py --processed <path to cotton-candy/processed>  [--quick]

Writes validation_report.md (or validation_report_quick.md with --quick) next to this script.
Policy values use the EXPECTED outcome from the answer key (no noise), on the TEST curves. Numbers that
depend on random draws are reported as mean +- sd over several seeds.
"""
import argparse
import os
import numpy as np
import pandas as pd

from ccgen import Config, load_curves, generate
from ccgen.config import SCENARIOS

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_WEIGHT = (7.1, 8.6, 9.7)          # p10, median, p90 of the real measured weights (152 valid runs)
TEMP_BINS = [0, 55, 60, 65, 70, 75, 80, 95]


def pct(s):
    return tuple(float(v) for v in np.percentile(s, [10, 50, 90]).round(1))


def ms(values, digits=2):
    v = np.asarray(values, dtype=float)
    return f"{v.mean():.{digits}f} +- {v.std():.{digits}f}" if len(v) > 1 else f"{v.mean():.{digits}f}"


def cold_start(curves, tabs):
    """Does the generated operator react to a cold machine like the real one (batches 0-14)?"""
    c = tabs["cases"].merge(tabs["case_truth"][["case_id", "arm"]], on="case_id").query("arm == 'fixed_wait'")
    hr = {x.curve_id: x.head_at_ready for x in curves}
    gen = np.corrcoef(c.curve_id.map(hr), c.t_start - c.t_ready)[0, 1]
    fr = [x for x in curves if not x.real_controller]
    real = np.corrcoef([x.head_at_ready for x in fr], [x.real_wait for x in fr])[0, 1]
    return gen, real


def realism(curves, tabs):
    c = tabs["cases"].merge(tabs["case_truth"][["case_id", "arm"]], on="case_id")
    c["wait"] = c.t_start - c.t_ready
    loop = [x for x in curves if x.real_controller and x.loop_ran]
    fixed = [x for x in curves if not x.real_controller]
    return [
        ("controller arm: head reading at start (C)", pct(c[c.arm == "controller"].head_start),
         pct([np.interp(x.t_real_start, x.x, x.head) for x in loop])),
        ("controller arm: wait after stick placed (s)", pct(c[c.arm == "controller"].wait),
         pct([x.real_wait for x in curves if x.real_controller])),
        ("fixed-wait arm: wait after stick placed (s)", pct(c[c.arm == "fixed_wait"].wait),
         pct([x.real_wait for x in fixed])),
        ("observed weight (g)", pct(c.weight), REAL_WEIGHT),
    ]


def weight_by_temperature(curves, tabs, processed):
    """Mean weight by head reading at the start: real runs vs generated cases (historical arms only)."""
    runs = pd.read_csv(os.path.join(processed, "runs.csv"))
    real = pd.DataFrame([(x.curve_id, np.interp(x.t_real_start, x.x, x.head)) for x in curves],
                        columns=["instance", "h"]).merge(runs[["instance", "weight"]], on="instance")
    real = real[(real.weight > 3) & (real.weight < 15)]     # 17.4 g (run 64570) is an outlier
    g = tabs["cases"].merge(tabs["case_truth"][["case_id", "arm"]], on="case_id").query("arm != 'random'")
    rb = real.groupby(pd.cut(real.h, TEMP_BINS), observed=False).weight.agg(["mean", "size"])
    gb = g.groupby(pd.cut(g.head_start, TEMP_BINS), observed=False).weight.mean()
    return rb, gb


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
    return truth, l.mean() - e.mean()


def trailing_mean(x, v, width=10.0):
    """Mean of the readings in the last `width` seconds (a method may compute this online)."""
    lo = np.searchsorted(x, x - width)
    c = np.concatenate([[0.0], np.cumsum(v)])
    idx = np.arange(len(v)) + 1
    return (c[idx] - c[lo]) / (idx - lo)


def first_at_least(values, threshold):
    hit = np.nonzero(values >= threshold)[0]
    return hit[0] if len(hit) else len(values) - 1


def baselines(cases):
    """Policy values on the test cases (expected KPI, averaged over cases). Thresholds act on what a method
    can see: the current reading, or the mean of the readings in the last 10 s."""
    test = [cs for cs in cases if cs["split"] == "test"]
    delays = np.arange(0, 121, 10)
    thresholds = np.arange(46, 90, 1)
    v = {"historical policy": [], "oracle": [], "observable oracle": []}
    by_delay = {d: [] for d in delays}
    by_raw = {T: [] for T in thresholds}
    by_avg = {T: [] for T in thresholds}
    for cs in test:
        st, ey = cs["st"], cs["ey"]
        avg = trailing_mean(cs["curve"].x, cs["curve"].head)[st["idx"]]
        v["historical policy"].append(ey[cs["k_start"]])
        v["oracle"].append(ey.max())
        v["observable oracle"].append(ey[int(np.argmax(cs["ey_obs"]))])
        for d in delays:
            by_delay[d].append(ey[first_at_least(st["t_rel"], d)])
        for T in thresholds:
            by_raw[T].append(ey[first_at_least(st["head"], T)])
            by_avg[T].append(ey[first_at_least(avg, T)])
    res = {k: float(np.mean(x)) for k, x in v.items()}
    res["best fixed delay"] = max(np.mean(x) for x in by_delay.values())
    res["best threshold, current reading"] = max(np.mean(x) for x in by_raw.values())
    res["best threshold, 10 s mean"] = max(np.mean(x) for x in by_avg.values())
    res["best is the first moment (share)"] = float(np.mean([np.argmax(cs["ey"]) == 0 for cs in test]))
    return res


def run(curves, seeds, resamples, **kw):
    """Baselines and naive error for one configuration, over several seeds."""
    out = []
    for s in seeds:
        cfg = Config(**kw, seed=s, resamples_per_curve=resamples)
        cases, tabs = generate(curves, cfg)
        b = baselines(cases)
        tr, nv = naive_vs_truth(tabs)
        b["naive error"] = nv - tr
        out.append(b)
    return {k: [o[k] for o in out] for k in out[0]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--processed", required=True)
    ap.add_argument("--quick", action="store_true", help="one seed, fewer resamples, no sweeps")
    args = ap.parse_args()
    curves = load_curves(args.processed)
    seeds = [0] if args.quick else [0, 1, 2]
    res = 5 if args.quick else 10
    cfg = Config(resamples_per_curve=5 if args.quick else 20)
    cases, tabs = generate(curves, cfg)
    out = ["# Validation report", "", f"Config: `{cfg.to_dict()}`", "",
           f"{len(tabs['cases'])} cases from {len(curves)} real curves "
           f"({sum(c.real_controller for c in curves)} from controller batches); decision points per case "
           f"{pct(tabs['answer_key'].groupby('case_id').size())} (p10 / median / p90).", ""]

    out += ["## 1. Realism (generated vs real, p10 / median / p90)", "", "| Quantity | Generated | Real |", "|---|---|---|"]
    for name, g, r in realism(curves, tabs):
        out.append(f"| {name} | {g} | {r} |")
    gen_r, real_r = cold_start(curves, tabs)
    out += ["", f"Fixed-wait arm, correlation between head temperature at \"stick placed\" and waiting time: "
            f"generated {gen_r:+.2f}, real {real_r:+.2f} (cold machines wait longer)."]
    rb, gb = weight_by_temperature(curves, tabs, args.processed)
    out += ["", "Mean weight by head reading at the start (real runs vs generated historical cases). The outcome is",
            "specified, not fitted; the real comparison is small, confounded and almost flat (one 17.4 g outlier",
            "excluded), so it is a sanity check only.", "",
            "| Head at start | " + " | ".join(str(i) for i in rb.index) + " |", "|---" * (len(rb) + 1) + "|",
            "| Real (g) | " + " | ".join(f"{m:.2f} (n={n})" for m, n in zip(rb["mean"], rb["size"])) + " |",
            "| Generated (g) | " + " | ".join(f"{v:.2f}" for v in gb) + " |"]

    main_runs = run(curves, seeds, res)
    out += ["", f"## 2. Baselines and confounding (realistic defaults; mean +- sd over seeds {seeds})", "",
            "| Quantity | Value |", "|---|---|"]
    for k in ["historical policy", "best fixed delay", "best threshold, current reading", "best threshold, 10 s mean",
              "oracle", "best is the first moment (share)", "naive error"]:
        out.append(f"| {k} | {ms(main_runs[k])} |")
    out += ["", "Naive error = (naive estimate - truth) of the effect of waiting 10-40 s instead of 0-4 s."]

    if not args.quick:
        def table(title, key, values, extra=None):
            rows = ["", title, "", f"| {key} | historical | best threshold, current reading | best threshold, 10 s mean | "
                    "oracle | naive error |", "|---|---|---|---|---|---|"]
            for val in values:
                r = run(curves, seeds, res, **{key: val}, **(extra or {}))
                rows.append(f"| {val} | {ms(r['historical policy'])} | {ms(r['best threshold, current reading'])} | "
                            f"{ms(r['best threshold, 10 s mean'])} | {ms(r['oracle'])} | {ms(r['naive error'])} |")
            return rows

        out += ["", "## 3. Knobs"]
        out += table("Share following the real batch policy, delta (the rest starts at a random moment):", "delta",
                     [0.0, 0.5, 0.95, 1.0])
        out += table("Width of the outcome window w (C); W_max fixed:", "w", [20.0, 30.0, 40.0, 60.0])
        out += table("Optimal head temperature h0 (C):", "h0", [60.0, 65.0, 70.0])
        out += table("Wear effect on the optimum a_wear (C per 30 candies):", "a_wear", [0.0, 8.0, 16.0])

        out += ["", "## 4. Scenarios (generate.py --scenario NAME)", "",
                "| scenario | historical | best threshold, current reading | best threshold, 10 s mean | "
                "observable oracle | oracle | naive error |", "|---|---|---|---|---|---|---|"]
        for name, kw in SCENARIOS.items():
            r = run(curves, seeds, res, **kw)
            out.append(f"| {name} | {ms(r['historical policy'])} | {ms(r['best threshold, current reading'])} | "
                       f"{ms(r['best threshold, 10 s mean'])} | {ms(r['observable oracle'])} | {ms(r['oracle'])} | "
                       f"{ms(r['naive error'])} |")

    report = "\n".join(out)
    print(report)
    name = "validation_report_quick.md" if args.quick else "validation_report.md"
    with open(os.path.join(HERE, name), "w") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    main()
