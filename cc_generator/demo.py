"""What is the benchmark for?  A walk-through with three simple "methods".

    python demo.py --processed ../datasets/cotton-candy/processed

The idea in one sentence: a method may only learn from the OBSERVED log (one start moment and one
weight per candy), and we then grade its advice with the hidden ANSWER KEY (the weight for every
possible start moment). On real data that grading step is impossible.

The methods:
  A.  Event-only, naive: learns "how long to wait" from the log, ignoring the sensor.
  A'. The same method A on a log where the operator started at random (delta = 0), to show that
      A's failure comes from the operator's habit (confounding), not from the method.
  B.  Sensor-aware: learns how the weight depends on the head temperature at the start,
      and gives every candy its own target temperature.
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
    args = ap.parse_args()

    # =========================================================================================
    title("STEP 1  Generate the benchmark")
    # =========================================================================================
    cfg = Config()
    curves = load_curves(args.processed, verbose=False)
    tabs = generate(curves, cfg)[1]
    cases, dp = tabs["cases"], tabs["decision_points"]           # OBSERVED: methods may use these
    key, truth = tabs["answer_key"], tabs["case_truth"]          # HIDDEN: only for grading
    say(f"{len(cases)} candies. Observed: one start moment + one weight per candy.")
    say("Hidden: the weight for EVERY possible start moment (the answer key).")

    # =========================================================================================
    title("STEP 2  One candy, seen two ways")
    # =========================================================================================
    one = cases[cases.split == "test"].iloc[0]
    k1 = key[key.case_id == one.case_id]
    best = k1.loc[k1.expected_y.idxmax()]
    say(f"Candy {one.case_id}. The (simulated) operator started {one.t_start - one.t_ready:.0f} s after the")
    say(f"stick was placed, at {one.head_start:.1f} C, and got {one.y:.2f} g. That is ALL a real log would show.")
    say("\nThe answer key also knows what other start moments would have given:")
    say("   wait   head    weight (expected)")
    for _, r in k1.iloc[::5].iterrows():
        mark = "  <- observed" if r.point == one.start_point else ""
        say(f"  {r.t - one.t_ready:4.0f} s  {r['head']:5.1f} C  {r.expected_y:6.2f} g{mark}")
    say(f"Best for this candy: wait {best.t - one.t_ready:.0f} s (head {best['head']:.1f} C) -> {best.expected_y:.2f} g.")

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

    def naive_by_wait(log):
        log = log.assign(wait=log.t_start - log.t_ready)
        log["bin"] = pd.cut(log.wait, WAIT_BINS, right=False, labels=False)
        return log.groupby("bin").y.agg(["mean", "size"])

    # =========================================================================================
    title("STEP 3  Method A: event-only, naive")
    # =========================================================================================
    say("Method A looks at the training log: how much candy came out, by how long the operator waited?")
    say("It then picks the waiting time with the most candy. Next to its estimate we show the TRUE value")
    say("of always waiting that long, which only the answer key can tell.\n")
    naive = naive_by_wait(train)
    say("   operator waited   log says          truth")
    for b, r in naive.iterrows():
        b = int(b)
        say(f"  {WAIT_LABELS[b]:>14}   {r['mean']:5.2f} g ({int(r['size']):4d})   {true_delay[b]:5.2f} g")
    b_a = int(naive["mean"].idxmax())
    say(f"\nConclusion of method A: start right away ({WAIT_LABELS[b_a]}). The truth says waiting helps.")
    say("Why: the operator starts as soon as the head is warm. Candies that started right away were on")
    say("heads that were already warm, so they did well anyway; late starters were on slow, cold heads,")
    say("so they did badly anyway. The log mixes up 'waited longer' with 'slow machine' (confounding).")
    pol_a = first_point_where(test_key, test_key.wait >= BIN_TARGET[b_a])
    results.append(grade(pol_a, test_key, f"A  event-only, naive (wait {WAIT_LABELS[b_a]})"))

    # =========================================================================================
    title("STEP 4  Same method A, but on a log where the operator started at random")
    # =========================================================================================
    say("Proof that the trap is the operator's habit and not the method: regenerate the log with")
    say("delta = 0 (every start moment random, like an experiment) and run the identical method.")
    say("This log is 5x larger, because random starts spread thin over the waiting times.\n")
    rct = generate(curves, Config(delta=0.0, resamples_per_curve=100))[1]["cases"]   # bigger log: random starts spread thin
    naive_rct = naive_by_wait(rct[rct.split == "train"])
    say("   operator waited   random log says   truth")
    for b, r in naive_rct.iterrows():
        b = int(b)
        say(f"  {WAIT_LABELS[b]:>14}   {r['mean']:5.2f} g ({int(r['size']):4d})   {true_delay[b]:5.2f} g")
    b_r = int(naive_rct["mean"].idxmax())
    b_true = max(true_delay, key=true_delay.get)
    verdict = "exactly the true best" if b_r == b_true else f"much closer to the true best ({WAIT_LABELS[b_true]})"
    say(f"\nNow method A picks {WAIT_LABELS[b_r]}: {verdict}.")
    say("Its estimates follow the truth instead of contradicting it. With real (non-random) logs you never")
    say("get this; a good prescriptive method must undo the operator's habit itself. The benchmark can")
    say("check whether it does, by turning the habit (delta) up and down.")
    pol_r = first_point_where(test_key, test_key.wait >= BIN_TARGET[b_r])
    results.append(grade(pol_r, test_key, f"A' event-only, on a random log (wait {WAIT_LABELS[b_r]})"))

    # =========================================================================================
    title("STEP 5  Method B: sensor-aware, personal target temperature")
    # =========================================================================================
    say("Model the weight as a function of the head temperature at the start, the time, and the case")
    say("(wear, humidity), with interaction terms so each candy can have its own best temperature.")
    hum_mu, hum_sd = train.env_hum.mean(), train.env_hum.std()

    def features(head, t, wear, hum):
        hz = (np.nan_to_num(hum, nan=hum_mu) - hum_mu) / hum_sd
        wz = (wear - 30) / 30
        hc = head - 64
        return np.column_stack([np.ones(len(head)), hc, hc ** 2, hc * wz, hc * hz, wz, hz, t])

    Xc = features(train.head_start.values, train.t_start.values, train.wear.values, train.env_hum.values)
    coef, *_ = np.linalg.lstsq(Xc, train.y.values, rcond=None)
    # best temperature = top of the fitted parabola in head, per case
    wz = (test_key.wear - 30) / 30
    hz = (test_key.env_hum.fillna(hum_mu) - hum_mu) / hum_sd
    target = 64 - (coef[1] + coef[3] * wz + coef[4] * hz) / (2 * coef[2])
    test_key["target"] = target
    say(f"Learned: target = 64 C {-(coef[3]) / (2 * coef[2]):+.1f} per wear step "
        f"{-(coef[4]) / (2 * coef[2]):+.1f} per humidity SD  (truth: +8 and -4)")
    say("Rule: start at the first decision point where the head reaches this candy's target.")
    say("B is not fooled by the operator's habit: the habit depended on the head temperature, and B")
    say("compares candies at the SAME temperature, so slow and fast machines are no longer mixed up.")
    pol_c = first_point_where(test_key, test_key["head"] >= test_key.target)
    results.append(grade(pol_c, test_key, "B  sensor-aware, personal target"))

    oracle = test_key.groupby("case_id").expected_y.max().mean()
    results.append(("Oracle (best moment per candy, needs the answer key)", oracle))

    # =========================================================================================
    title("STEP 6  The grades (test candies, true expected weight per candy)")
    # =========================================================================================
    hist = results[0][1]
    for label, v in results:
        bar = "#" * int(round((v - 7.0) * 20))
        say(f"  {label:<55} {v:5.2f} g  {v - hist:+.2f}  {bar}")
    say("\nWhat this shows:")
    say("  - Learning naively from the log (A) gives advice that is WORSE than the operators.")
    say("  - The same method on a random log (A') does better: the trap is confounding.")
    say("    Even then, one fixed delay for every candy leaves a lot on the table.")
    say("  - Watching the temperature and personalizing (B) gets close to the best possible.")
    say("None of these grades could be computed on the real log: that is what the benchmark is for.")


if __name__ == "__main__":
    main()
