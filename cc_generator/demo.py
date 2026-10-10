"""What is the benchmark for?  A walk-through with three simple "methods".

    python demo.py --processed ../datasets/cotton-candy/processed

The idea in one sentence: a method may only learn from the OBSERVED log (one start moment and one
weight per candy), and we then grade its advice with the hidden ANSWER KEY (the weight for every
possible start moment). On real data that grading step is impossible.

The methods:
  A.  Event-only, naive: learns "how long to wait" from the log, ignoring the sensor.
  A'. The same method A on a log where every start moment was random (delta = 0, like an experiment),
      to show what the operators' habits (confounding) do to A.
  B.  Sensor-aware: learns how the weight depends on the head reading at the start, and gives every
      candy its own target reading.
"""
import argparse
import numpy as np
import pandas as pd

from ccgen import Config, load_curves, generate


def say(text=""):
    print(text)


def title(text):
    print("\n" + "=" * 78 + "\n" + text + "\n" + "=" * 78)


# ---------------------------------------------------------------------------------------------
# Helpers a method may use (they only touch observed data)
# ---------------------------------------------------------------------------------------------
WAIT_BINS = [0, 4, 10, 20, 30, 40, 60, 1000]          # seconds after the stick is placed
WAIT_LABELS = ["0-4 s", "4-10 s", "10-20 s", "20-30 s", "30-40 s", "40-60 s", "60+ s"]
BIN_TARGET = [0, 6, 14, 24, 34, 48, 70]                # the delay a method "means" by each bin


# ---------------------------------------------------------------------------------------------
# Grading: turn a policy into start moments on the TEST cases and look the outcomes up
# ---------------------------------------------------------------------------------------------
def grade(policy_start_point, key, label):
    """policy_start_point: Series case_id -> chosen decision point. Returns the mean TRUE outcome."""
    chosen = key.merge(policy_start_point.rename("chosen").reset_index(), on="case_id")
    chosen = chosen[chosen.point == chosen.chosen]
    return label, chosen.expected_y.mean()


def first_point_where(key, condition):
    """Online rule: start at the first decision point where `condition` holds (else the last point).
    A rule like this only looks at the present, never at future sensor values."""
    k = key.assign(ok=condition).sort_values(["case_id", "point"])
    last = k.groupby("case_id").point.max()
    first_ok = k[k.ok].groupby("case_id").point.min()
    return first_ok.reindex(last.index).fillna(last).astype(int)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--processed", required=True)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="override a Config knob")
    args = ap.parse_args()
    over = {k: float(v) for k, v in (kv.split("=", 1) for kv in args.set)}

    # =========================================================================================
    title("STEP 1  Generate the benchmark")
    # =========================================================================================
    cfg = Config(**over)
    curves = load_curves(args.processed, verbose=False)
    tabs = generate(curves, cfg)[1]
    cases, dp = tabs["cases"], tabs["decision_points"]           # OBSERVED: methods may use these
    key, truth = tabs["answer_key"], tabs["case_truth"]          # HIDDEN: only for grading
    say(f"{len(cases)} candies. Observed: one start moment + one weight per candy, and the sensor readings.")
    say("Hidden: the weight for EVERY possible start moment (the answer key).")

    # =========================================================================================
    title("STEP 2  One candy, seen two ways")
    # =========================================================================================
    one = cases[cases.split == "test"].iloc[0]
    k1 = key[key.case_id == one.case_id]
    best = k1.loc[k1.expected_y.idxmax()]
    say(f"Candy {one.case_id}. The (simulated) operator started {one.t_start - one.t_ready:.0f} s after the")
    say(f"stick was placed, at a reading of {one.head_start:.1f} C, and got {one.y:.2f} g. That is ALL a real log")
    say("would show (plus the sensor readings up to the start).")
    say("\nThe answer key also knows what every other start moment would have given:")
    say("   wait   reading   weight (expected)")
    for _, r in k1.iloc[::6].iterrows():
        mark = "  <- observed" if r.point == one.start_point else ""
        say(f"  {r.t - one.t_ready:4.0f} s  {r['head']:6.1f} C  {r.expected_y:6.2f} g{mark}")
    say(f"Best for this candy: wait {best.t - one.t_ready:.0f} s (reading {best['head']:.1f} C) -> {best.expected_y:.2f} g.")
    say(f"Note the decision points: one per real sensor reading, here every "
        f"{np.median(np.diff(k1.t)):.1f} s (1.3-6.5 s depending on the batch).")

    train = cases[cases.split == "train"].copy()
    test_key = key[key.case_id.isin(cases.case_id[cases.split == "test"])].copy()
    test_key = test_key.merge(cases[["case_id", "t_ready", "wear", "env_hum"]], on="case_id")
    test_key["wait"] = test_key.t - test_key.t_ready

    results = []
    test_hist = cases[cases.split == "test"].set_index("case_id").start_point
    results.append(grade(test_hist, test_key, "Historical operators (what happened)"))

    # the TRUE value of "always wait d seconds" on the test candies (needs the answer key)
    true_delay = {b: grade(first_point_where(test_key, test_key.wait >= BIN_TARGET[b]), test_key, "")[1]
                  for b in range(len(BIN_TARGET))}
    b_true = max(true_delay, key=true_delay.get)

    def naive_by_wait(log):
        log = log.assign(wait=log.t_start - log.t_ready)
        log["bin"] = pd.cut(log.wait, WAIT_BINS, right=False, labels=False)
        return log.groupby("bin").y.agg(["mean", "size"])

    def show(table, header):
        say(f"   operator waited   {header:<16}  truth")
        for b, r in table.iterrows():
            b = int(b)
            say(f"  {WAIT_LABELS[b]:>14}   {r['mean']:5.2f} g ({int(r['size']):4d})   {true_delay[b]:5.2f} g")

    # =========================================================================================
    title("STEP 3  Method A: event-only, naive")
    # =========================================================================================
    say("Method A looks at the training log: how much candy came out, by how long the operator waited?")
    say("It then picks the waiting time with the most candy. Next to its estimate we show the TRUE value")
    say("of always waiting that long, which only the answer key can tell.\n")
    naive = naive_by_wait(train)
    show(naive, "log says")
    b_a = int(naive["mean"].idxmax())
    say(f"\nMethod A picks {WAIT_LABELS[b_a]}; the true best fixed wait is {WAIT_LABELS[b_true]}.")
    say("Where the log and the truth disagree, that is confounding: the operators' habits depend on the")
    say("machine (the temperature controller starts at once on a warm head; the early batches waited longer")
    say("on other days). The log mixes up 'waited longer' with 'different machine state'.")
    pol_a = first_point_where(test_key, test_key.wait >= BIN_TARGET[b_a])
    results.append(grade(pol_a, test_key, f"A  event-only, naive (wait {WAIT_LABELS[b_a]})"))

    # =========================================================================================
    title("STEP 4  Same method A, on a randomized log")
    # =========================================================================================
    say("Regenerate the log with delta = 0: every start moment is random, as in an experiment, so it does")
    say("not depend on the machine. Run the identical method on it.")
    say("This log is 5x larger, because random starts spread thin over the waiting times.\n")
    nc = generate(curves, Config(**{**over, 'delta': 0.0, 'resamples_per_curve': 100}))[1]["cases"]
    naive_nc = naive_by_wait(nc[nc.split == "train"])
    show(naive_nc, "random log")
    b_r = int(naive_nc["mean"].idxmax())
    say(f"\nNow method A picks {WAIT_LABELS[b_r]} (true best fixed wait: {WAIT_LABELS[b_true]}).")
    say("Random starts do not depend on the machine, so this log is not confounded; the remaining differences")
    say("with the truth come from training on other curves than the test curves. Real logs are never")
    say("randomized: a good prescriptive method must")
    say("undo the operators' habits itself, and turning delta up and down checks whether it does.")
    pol_r = first_point_where(test_key, test_key.wait >= BIN_TARGET[b_r])
    results.append(grade(pol_r, test_key, f"A' event-only, randomized log (wait {WAIT_LABELS[b_r]})"))

    # =========================================================================================
    title("STEP 5  Method B: sensor-aware, personal target reading")
    # =========================================================================================
    say("Model the weight as a function of the head reading at the start, the time since the stick was")
    say("placed, and the case (wear, humidity), with interaction terms so each candy can have its own")
    say("best reading.")
    hum_mu, hum_sd = train.env_hum.mean(), train.env_hum.std()
    H0 = 65.0

    def features(head, t_rel, wear, hum):
        hz = (np.nan_to_num(hum, nan=hum_mu) - hum_mu) / hum_sd
        wz = (wear - 30) / 30
        hc = head - H0
        return np.column_stack([np.ones(len(head)), hc, hc ** 2, hc * wz, hc * hz, wz, hz, t_rel])

    Xc = features(train.head_start.values, (train.t_start - train.t_ready).values, train.wear.values,
                  train.env_hum.values)
    coef, *_ = np.linalg.lstsq(Xc, train.y.values, rcond=None)
    wz = (test_key.wear - 30) / 30
    hz = (test_key.env_hum.fillna(hum_mu) - hum_mu) / hum_sd
    test_key["target"] = H0 - (coef[1] + coef[3] * wz + coef[4] * hz) / (2 * coef[2])
    say(f"Learned: target shifts {-(coef[3]) / (2 * coef[2]):+.1f} C per wear step and "
        f"{-(coef[4]) / (2 * coef[2]):+.1f} C per humidity SD  (truth: +8 and 0)")
    say("Rule: start at the first reading that reaches this candy's target.")
    say("B compares candies at the SAME head reading, so the controller's habit does not fool it.")
    pol_c = first_point_where(test_key, test_key["head"] >= test_key.target)
    results.append(grade(pol_c, test_key, "B  sensor-aware, personal target"))

    oracle = test_key.groupby("case_id").expected_y.max().mean()
    results.append(("Oracle (best moment per candy, needs the answer key)", oracle))

    # =========================================================================================
    title("STEP 6  The grades (test candies, true expected KPI per candy: weight minus time cost)")
    # =========================================================================================
    hist = results[0][1]
    low = min(v for _, v in results) - 0.2
    for label, v in results:
        bar = "#" * int(round((v - low) * 40))
        say(f"  {label:<55} {v:5.2f} g  {v - hist:+.2f}  {bar}")
    say("\nNone of these grades could be computed on the real log: that is what the benchmark is for.")


if __name__ == "__main__":
    main()
