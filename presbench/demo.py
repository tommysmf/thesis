"""What is the benchmark for?  A walk-through with simple "methods", for any adapter.

    python demo.py --adapter cotton_candy --data ../datasets/cotton-candy/processed [--set key=value]

A method may only learn from the OBSERVED log (one decision point and one outcome per case), and is then graded
with the hidden ANSWER KEY (the outcome of every possible decision point). On real data that is impossible.

The methods:
  A.  Event-only, naive: learns "how long to wait after the window opens" from the log, ignoring the sensor.
  A'. The same method on a randomized log (delta = 0), to show what the historical policy (confounding) does.
  B.  Sensor-aware: a quadratic regression of the KPI on the signal at the decision (and the adapter's
      model_attributes), intervening at the first reading that reaches its personal target.
"""
import argparse
import numpy as np
import pandas as pd

from adapters import get_adapter
from presbench import make_settings, generate

WAIT_FRACTIONS = [0, 0.05, 0.1, 0.2, 0.3, 0.45, 0.65, 10]   # bins as fractions of the median window length


def title(text):
    print("\n" + "=" * 78 + "\n" + text + "\n" + "=" * 78)


def grade(choice, key):
    """choice: Series case_id -> decision point. Mean TRUE expected KPI of those choices."""
    k = key.merge(choice.rename("chosen").reset_index(), on="case_id")
    return k[k.point == k.chosen].expected_y.mean()


def first_point_where(key, condition):
    """Online rule: the first decision point where `condition` holds (else the last point)."""
    k = key.assign(ok=condition).sort_values(["case_id", "point"])
    last = k.groupby("case_id").point.max()
    first_ok = k[k.ok].groupby("case_id").point.min()
    return first_ok.reindex(last.index).fillna(last).astype(int)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    args = ap.parse_args()
    over = {k: float(v) for k, v in (kv.split("=", 1) for kv in args.set)}
    A = get_adapter(args.adapter)
    sig, unit = A.signal_name, A.signal_unit

    title("STEP 1  Generate the benchmark")
    real = A.load(args.data, verbose=False)
    generated, tabs = generate(A, real, make_settings(A, **over))
    cases, key = tabs["cases"], tabs["answer_key"]
    print(f"{len(cases)} cases from {len(real)} real cases. Observed: one decision point and one outcome per case.")
    print("Hidden: the outcome of EVERY possible decision point (the answer key).")

    title("STEP 2  One case, seen two ways")
    one = cases[cases.split == "test"].iloc[0]
    k1 = key[key.case_id == one.case_id]
    best = k1.loc[k1.expected_y.idxmax()]
    print(f"Case {one.case_id}: the historical policy intervened {one.t_start - one.t_open:.0f} s after the window "
          f"opened, at {sig} = {one[sig + '_at_start']:.1f} {unit}; KPI y = {one.y:.2f}. A real log shows only this.")
    print("\nThe answer key knows every other decision point too:")
    print(f"   wait   {sig:>8}   expected KPI")
    for _, r in k1.iloc[::max(1, len(k1) // 9)].iterrows():
        mark = "  <- observed" if r.point == one.start_point else ""
        print(f"  {r.t - one.t_open:5.0f} s  {r[sig]:8.1f}   {r.expected_y:8.2f}{mark}")
    print(f"Best: wait {best.t - one.t_open:.0f} s ({sig} {best[sig]:.1f}) -> {best.expected_y:.2f}. "
          f"Decision points here: every {np.median(np.diff(k1.t)):.1f} s (the real sensor readings).")

    train = cases[cases.split == "train"].copy()
    test_key = key[key.case_id.isin(cases.case_id[cases.split == "test"])].merge(
        cases.drop(columns=["t_start"]), on="case_id")
    test_key["wait"] = test_key.t - test_key.t_open
    length = np.median([g["dp"].t_rel[-1] for g in generated])
    bins = [f * length for f in WAIT_FRACTIONS]
    labels = [f"{bins[i]:.0f}-{bins[i + 1]:.0f} s" if i < len(bins) - 2 else f"{bins[i]:.0f}+ s"
              for i in range(len(bins) - 1)]
    targets = [(bins[i] + min(bins[i + 1], 1.5 * length)) / 2 if i else 0.0 for i in range(len(bins) - 1)]
    results = [("Historical policy (what happened)", grade(cases[cases.split == "test"].set_index("case_id").start_point,
                                                          test_key))]
    truth = {b: grade(first_point_where(test_key, test_key.wait >= targets[b]), test_key) for b in range(len(targets))}

    def by_wait(log):
        log = log.assign(bin=pd.cut(log.t_start - log.t_open, bins, right=False, labels=False))
        return log.groupby("bin").y.agg(["mean", "size"])

    def show(table, header):
        print(f"   waited       {header:<18} truth")
        for b, r in table.iterrows():
            print(f"  {labels[int(b)]:>11}   {r['mean']:7.2f} ({int(r['size']):5d})   {truth[int(b)]:7.2f}")

    title("STEP 3  Method A: event-only, naive")
    naive = by_wait(train)
    show(naive, "log says")
    b_a = int(naive["mean"].idxmax())
    b_true = max(truth, key=truth.get)
    print(f"\nMethod A picks {labels[b_a]}; the true best fixed wait is {labels[b_true]}. Where the log and the truth")
    print("disagree, the historical policy's habits mix up 'waited longer' with 'a different case'.")
    results.append((f"A  event-only, naive ({labels[b_a]})",
                    grade(first_point_where(test_key, test_key.wait >= targets[b_a]), test_key)))

    title("STEP 4  Same method A, on a randomized log (delta = 0)")
    rnd = generate(A, real, make_settings(A, **{**over, "delta": 0.0, "resamples_per_case": 100}))[1]["cases"]
    naive_r = by_wait(rnd[rnd.split == "train"])
    show(naive_r, "random log says")
    b_r = int(naive_r["mean"].idxmax())
    print(f"\nNow method A picks {labels[b_r]} (true best: {labels[b_true]}). Random decisions do not depend on the")
    print("case, so this log is not confounded; remaining differences come from different train and test cases.")
    results.append((f"A' event-only, randomized log ({labels[b_r]})",
                    grade(first_point_where(test_key, test_key.wait >= targets[b_r]), test_key)))

    title("STEP 5  Method B: sensor-aware, personal target")
    attrs = [a for a in A.model_attributes if a in train.columns]
    stats = {a: (train[a].mean(), train[a].std() or 1.0) for a in attrs}
    center = float(train[sig + "_at_start"].median())

    def features(df, s_col):
        hc = df[s_col].to_numpy(float) - center
        zs = [(df[a].fillna(stats[a][0]).to_numpy(float) - stats[a][0]) / stats[a][1] for a in attrs]
        t = (df["t_start"] - df["t_open"]).to_numpy(float) if "t_start" in df else df["wait"].to_numpy(float)
        return np.column_stack([np.ones(len(hc)), hc, hc ** 2] + [hc * z for z in zs] + zs + [t])

    coef, *_ = np.linalg.lstsq(features(train, sig + "_at_start"), train.y.to_numpy(float), rcond=None)
    zs = [(test_key[a].fillna(stats[a][0]).to_numpy(float) - stats[a][0]) / stats[a][1] for a in attrs]
    test_key["target"] = center - (coef[1] + sum(coef[3 + i] * z for i, z in enumerate(zs))) / (2 * coef[2])
    for i, a in enumerate(attrs):
        print(f"Learned: the target moves {-coef[3 + i] / (2 * coef[2]):+.1f} {unit} per standard deviation of {a}")
    print("Rule: intervene at the first reading that reaches this case's target.")
    print("(The learned target is only meaningful if the KPI is curved in the signal; a flat fit gives odd targets.)")
    d = A.signal_direction                      # +1: the target is reached from below, -1: from above
    results.append(("B  sensor-aware, personal target",
                    grade(first_point_where(test_key, d * test_key[sig] >= d * test_key.target), test_key)))
    results.append(("Oracle (best point per case, needs the answer key)", test_key.groupby("case_id").expected_y.max().mean()))

    title("STEP 6  The grades (test cases, true expected KPI per case)")
    hist = results[0][1]
    lo, hi = min(v for _, v in results), max(v for _, v in results)
    scale = 50 / (hi - lo) if hi > lo else 0.0          # bars span 5-55 characters, whatever the KPI's units
    for label, v in results:
        print(f"  {label:<55} {v:9.2f}  {v - hist:+8.2f}  {'#' * int(round(5 + (v - lo) * scale))}")
    print("\nNone of these grades could be computed on a real log: that is what the benchmark is for.")


if __name__ == "__main__":
    main()
