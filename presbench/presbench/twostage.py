"""Two linked timing decisions per case: "when to do A" and then "when to do B", where B's window, and the signal
a method sees during it, depend on when A happened (for example: when to start spinning, then when to stop).

The single-decision core (generator.py, online.py) is unchanged; this module reuses its splits and random
draws. An adapter implements TwoStageAdapter (below). Per real case, resampled `resamples_per_case` times:

  1. stage 1: decision points = the real readings in [t_open, t_close], as in the single-decision core;
  2. for EVERY first decision point k1, the adapter says how the signal continues after acting at t1
     (signal_after) and where the second window is (second_window); stage-2 decision points are the readings of
     that signal inside it;
  3. random parts in a fixed order: hidden u, arm draw stage 1, outcome noise (as the core), arm draw stage 2,
     then the policies' own draws;
  4. each stage is decided by its historical policy with probability delta, else uniformly at random, so
         P(k1, k2) = pi1[k1] * pi2[k1][k2],  pi_s = delta * policy_s.distribution() + (1 - delta) / n_s;
  5. the outcome of EVERY path (k1, k2), and the same averaged over u if the outcome uses it.

Output files (S = signal_name, O = outcome_name):
  observed/event_log.csv        real events + intervention 1 + intervention 2 + the outcome event
  observed/sensor_stream.csv    the signal as it evolved under the historical first decision, up to the second
  observed/decision_points.csv  stage, point, t, S, acted: the decision points up to each intervention
  observed/cases.csv            per case: group, attributes, split, both chosen points, measured O, KPI y
  truth/answer_key.csv.gz       per case x (point1, point2): times, signal, P(path), expected O and y, is_best
  truth/answer_key_first.csv    per case x point1: P(point1), best second point and its value, policy average
  truth/case_truth.csv          per case: arms, settings, hidden, best path, regret, noise
"""
import os
import json
import numpy as np
import pandas as pd

from .adapter import Adapter
from .case import DecisionPoints
from .generator import split_cases, draw_case, U_NODES, U_WEIGHTS, _locf


class TwoStageAdapter(Adapter):
    """Contract for two linked decisions. On top of the Adapter attributes:

    stage_names = (name 1, name 2), used in reports; intervention_activities = (activity 1, activity 2)
    load(path)                        -> list of RealCase; t_open/t_close is the FIRST window
    signal_after(case, t1)            -> signal at case.times if intervention 1 happened at t1: equal to
                                         case.signal for times <= t1 (nothing has changed yet)
    second_window(case, t1)           -> (t_open2, t_close2): the second window given t1 (t_open2 > t1)
    policy(cases, params)             -> (policy1, policy2), each a HistoricalPolicy: policy1 sees the stage-1
                                         DecisionPoints, policy2 the stage-2 ones (t_rel since t_open2)
    outcome(params)                   -> a TwoStageOutcome
    """
    stage_names = ("first", "second")
    intervention_activities = ("Intervene 1", "Intervene 2")

    def signal_after(self, case, t1):
        raise NotImplementedError

    def second_window(self, case, t1):
        raise NotImplementedError


class TwoStageOutcome:
    """expected(case, dp1, k1, dp2, hidden) -> (measure, kpi): arrays over the stage-2 points, without noise.
    truth_info(case, hidden) -> extra columns for case_truth.csv. uses_hidden: True if expected uses `hidden`."""
    uses_hidden = False

    def expected(self, case, dp1, k1, dp2, hidden):
        raise NotImplementedError

    def truth_info(self, case, hidden):
        return {}


def second_points(case, signal, t_open2, t_close2):
    """Stage-2 decision points: the readings of `signal` (at case.times) inside [t_open2, t_close2]."""
    idx = np.nonzero((case.times >= t_open2) & (case.times <= t_close2))[0]
    return DecisionPoints(idx=idx, t=case.times[idx], t_rel=case.times[idx] - t_open2, signal=signal[idx])


class RealCaseCache:
    """What does not change between resamples of one real case: stage-1 points, and per first point the signal,
    the stage-2 points and both policies' distributions (they use observable information only)."""

    def __init__(self, adapter, case, settings, policy1, policy2):
        self.dp1 = dp1 = case.decision_points()
        self.signal2, self.dp2, self.dist2 = [], [], []
        for t1 in dp1.t:
            sig = np.asarray(adapter.signal_after(case, float(t1)), dtype=float)
            dp2 = second_points(case, sig, *adapter.second_window(case, float(t1)))
            if len(dp2) == 0:
                raise ValueError(f"case {case.case_id}: no second-stage decision point after t1 = {t1}")
            self.signal2.append(sig)
            self.dp2.append(dp2)
            self.dist2.append(settings.delta * policy2.distribution(case, dp2) + (1 - settings.delta) / len(dp2))
        self.pi1 = settings.delta * policy1.distribution(case, dp1) + (1 - settings.delta) / len(dp1)
        self.outcomes = {}

    def outcome(self, case, outcome, hidden):
        """(measure, kpi) lists over k1; cached when the outcome does not use the hidden factor."""
        key = hidden if outcome.uses_hidden else None
        if key not in self.outcomes:
            res = [outcome.expected(case, self.dp1, k1, self.dp2[k1], hidden) for k1 in range(len(self.dp1))]
            self.outcomes[key] = ([np.asarray(m, float) for m, _ in res], [np.asarray(y, float) for _, y in res])
            if outcome.uses_hidden:
                self.outcomes = {key: self.outcomes[key]}        # keep memory flat: one hidden draw at a time
        return self.outcomes[key]

    def observable_kpi(self, case, outcome):
        if not outcome.uses_hidden:
            return self.outcome(case, outcome, 0.0)[1]
        if "obs" not in self.__dict__:
            acc = None
            for u, w in zip(U_NODES, U_WEIGHTS):
                kpi = [np.asarray(y, float) for _, y in
                       (outcome.expected(case, self.dp1, k1, self.dp2[k1], u) for k1 in range(len(self.dp1)))]
                acc = [w * y for y in kpi] if acc is None else [a + w * y for a, y in zip(acc, kpi)]
            self.obs = acc
        return self.obs


def _draw_stage(policy, case, dp, hidden, u_arm, delta, rng):
    if u_arm < delta:
        return policy.sample(case, dp, hidden, rng)
    return "random", np.nan, int(rng.integers(len(dp)))


def build_case(case, rep, settings, rng, split, policies, outcome, cache):
    """One generated case: both historical decisions and the outcome of every path."""
    d = draw_case(settings, rng)
    u_arm2 = rng.random()
    p1, p2 = policies
    arm1, set1, k1 = _draw_stage(p1, case, cache.dp1, d["hidden"], d["u_arm"], settings.delta, rng)
    arm2, set2, k2 = _draw_stage(p2, case, cache.dp2[k1], d["hidden"], u_arm2, settings.delta, rng)
    measure, kpi = cache.outcome(case, outcome, d["hidden"])
    return dict(case_id=f"{case.case_id}-{rep:03d}", case=case, rep=rep, split=split, cache=cache,
                k1=k1, k2=k2, arm1=arm1, setting1=set1, arm2=arm2, setting2=set2, hidden=d["hidden"],
                measure=measure, kpi=kpi, kpi_obs=cache.observable_kpi(case, outcome),
                truth_info=outcome.truth_info(case, d["hidden"]), noise=d["noise"])


def best_path(kpi):
    """(k1, k2, value) of the best path in a list (over k1) of arrays (over k2)."""
    v = [float(np.max(y)) for y in kpi]
    k1 = int(np.argmax(v))
    return k1, int(np.argmax(kpi[k1])), v[k1]


def generate(adapter, cases, settings):
    """Generate all cases. Returns (generated cases as dicts, tables as DataFrames)."""
    rng = np.random.default_rng(settings.seed + 1)
    splits = split_cases(cases, settings)
    policies = adapter.policy(cases, settings.params)
    outcome = adapter.outcome(settings.params)
    generated = []
    for c in cases:
        cache = RealCaseCache(adapter, c, settings, *policies)
        for rep in range(settings.resamples_per_case):
            generated.append(build_case(c, rep, settings, rng, splits[c.case_id], policies, outcome, cache))
    return generated, tables(adapter, generated)


def tables(adapter, generated):
    sig, out = adapter.signal_name, adapter.outcome_name
    act1, act2 = adapter.intervention_activities
    cases, dps, firsts, truths, logs, sensors, keys = [], [], [], [], [], [], []
    for g in generated:
        c, cache, k1, k2 = g["case"], g["cache"], g["k1"], g["k2"]
        dp1, dp2, s2 = cache.dp1, cache.dp2[k1], cache.signal2[k1]
        t1, t2 = float(dp1.t[k1]), float(dp2.t[k2])
        base = c.t0 + pd.Timedelta(days=g["rep"])
        measured = float(g["measure"][k1][k2] + g["noise"])
        y = float(g["kpi"][k1][k2] + g["noise"])
        cases.append(dict(case_id=g["case_id"], real_case_id=c.case_id, split=g["split"], group=c.group,
                          **c.attributes, t_open=c.t_open, first_point=k1, t_first=t1,
                          **{f"{sig}_at_first": dp1.signal[k1]}, second_point=k2, t_second=t2,
                          **{f"{sig}_at_second": dp2.signal[k2], out: measured, "y": y}))
        for stage, dp, k in [(1, dp1, k1), (2, dp2, k2)]:
            for j in range(k + 1):
                dps.append({"case_id": g["case_id"], "stage": stage, "point": j, "t": dp.t[j], sig: dp.signal[j],
                            "acted": int(j == k)})
        b1, b2, vbest = best_path(g["kpi"])
        o1, o2, _ = best_path(g["kpi_obs"])
        policy_avg = float(sum(cache.pi1[j] * np.dot(cache.dist2[j], g["kpi"][j]) for j in range(len(dp1))))
        truths.append(dict(case_id=g["case_id"], arm1=g["arm1"], setting1=g["setting1"], arm2=g["arm2"],
                           setting2=g["setting2"], hidden=g["hidden"], **g["truth_info"],
                           best_point1=b1, best_point2=b2, t_best1=cache.dp1.t[b1], t_best2=cache.dp2[b1].t[b2],
                           expected_y_best=vbest, expected_y_historical=g["kpi"][k1][k2],
                           regret=vbest - g["kpi"][k1][k2],
                           expected_y_best_second_given_first=float(np.max(g["kpi"][k1])),
                           best_point1_observable=o1, best_point2_observable=o2,
                           expected_y_best_observable=g["kpi"][o1][o2], expected_y_policy_average=policy_avg,
                           noise=g["noise"]))
        n1 = len(dp1)
        firsts.append(pd.DataFrame({
            "case_id": g["case_id"], "point1": np.arange(n1), "t1": dp1.t, f"{sig}_1": dp1.signal,
            "p_first": cache.pi1,
            "best_point2": [int(np.argmax(y)) for y in g["kpi"]],
            "expected_y_best_second": [float(np.max(y)) for y in g["kpi"]],
            "expected_y_policy_second": [float(np.dot(cache.dist2[j], g["kpi"][j])) for j in range(n1)]}))
        lens = [len(cache.dp2[j]) for j in range(n1)]
        p1 = np.repeat(np.arange(n1), lens)
        kpi_all = np.concatenate(g["kpi"])
        keys.append(pd.DataFrame({
            "case_id": g["case_id"], "point1": p1, "point2": np.concatenate([np.arange(n) for n in lens]),
            "t1": dp1.t[p1], "t2": np.concatenate([cache.dp2[j].t for j in range(n1)]),
            f"{sig}_1": dp1.signal[p1], f"{sig}_2": np.concatenate([cache.dp2[j].signal for j in range(n1)]),
            "p_path": np.concatenate([cache.pi1[j] * cache.dist2[j] for j in range(n1)]),
            f"expected_{out}": np.concatenate(g["measure"]), "expected_y": kpi_all,
            "expected_y_observable": np.concatenate(g["kpi_obs"]), "y_if_path": kpi_all + g["noise"],
            "is_best": ((p1 == b1) & (np.concatenate([np.arange(n) for n in lens]) == b2)).astype(int)}))
        for _, e in c.events.iterrows():
            logs.append({"case_id": g["case_id"], "t": e.t, "timestamp": base + pd.Timedelta(seconds=e.t),
                         "activity": e.activity, out: np.nan})
        t_fin = t2 + adapter.outcome_delay
        for t, a, v in [(t1, act1, np.nan), (t2, act2, np.nan), (t_fin, adapter.outcome_activity, measured)]:
            logs.append({"case_id": g["case_id"], "t": t, "timestamp": base + pd.Timedelta(seconds=t),
                         "activity": a, out: v})
        first = c.events.t.min() if len(c.events) else -60.0
        m = (c.times >= min(first, 0.0)) & (c.times <= t2)
        extra = {name: _locf(np.asarray(ct), cv, c.times[m]) for name, (ct, cv) in c.channels.items()}
        sensors.append(pd.DataFrame({"case_id": g["case_id"], "t": c.times[m],
                                     "timestamp": base + pd.to_timedelta(c.times[m], unit="s"), sig: s2[m],
                                     **extra}))
    return dict(cases=pd.DataFrame(cases), decision_points=pd.DataFrame(dps),
                answer_key=pd.concat(keys, ignore_index=True), answer_key_first=pd.concat(firsts, ignore_index=True),
                case_truth=pd.DataFrame(truths), event_log=pd.DataFrame(logs).sort_values(["case_id", "t"]),
                sensor_stream=pd.concat(sensors, ignore_index=True))


def write(tables_, settings, adapter, out_dir):
    obs, tru = os.path.join(out_dir, "observed"), os.path.join(out_dir, "truth")
    os.makedirs(obs, exist_ok=True)
    os.makedirs(tru, exist_ok=True)
    for name in ["event_log", "sensor_stream", "decision_points", "cases"]:
        tables_[name].to_csv(os.path.join(obs, f"{name}.csv"), index=False)
    tables_["answer_key"].to_csv(os.path.join(tru, "answer_key.csv.gz"), index=False)
    for name in ["answer_key_first", "case_truth"]:
        tables_[name].to_csv(os.path.join(tru, f"{name}.csv"), index=False)
    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump({"adapter": adapter.name, "decisions": list(adapter.stage_names), **settings.to_dict()}, f,
                  indent=2)


class TwoStageOnlineEnv:
    """Step through a case: first decide when to do intervention 1, then when to do intervention 2.

        env = TwoStageOnlineEnv(adapter, cases, settings, split="test")
        obs = env.reset()                 # obs["stage"] == 1
        while True:
            obs, reward, done, info = env.step(action)    # 1 = act now, 0 = wait
            if done: break
    After intervention 1 the observations come from the signal as it evolves after that decision
    (obs["stage"] == 2, obs["t_since_first"]). The last point of a window acts automatically.
    """

    def __init__(self, adapter, cases, settings, split="test", seed=None):
        splits = split_cases(cases, settings)
        self.cases = [c for c in cases if split is None or splits[c.case_id] == split]
        self.adapter, self.settings = adapter, settings
        self.policies = adapter.policy(cases, settings.params)
        self.outcome = adapter.outcome(settings.params)
        self.rng = np.random.default_rng(settings.seed + 2 if seed is None else seed)
        self._caches = {}

    def reset(self, case_index=None):
        if case_index is None:
            case_index = int(self.rng.integers(len(self.cases)))
        self.case = c = self.cases[case_index]
        if c.case_id not in self._caches:
            self._caches[c.case_id] = RealCaseCache(self.adapter, c, self.settings, *self.policies)
        self.cache = self._caches[c.case_id]
        d = draw_case(self.settings, self.rng)
        self.measure, self.kpi = self.cache.outcome(c, self.outcome, d["hidden"])
        self.noise = d["noise"]
        self.stage, self.k, self.k1 = 1, 0, None
        obs = self._obs()
        before = c.times < self.cache.dp1.t[0]
        obs["history"] = list(zip(c.times[before].tolist(), c.signal[before].tolist()))
        return obs

    def _dp(self):
        return self.cache.dp1 if self.stage == 1 else self.cache.dp2[self.k1]

    def _obs(self):
        c, dp, k = self.case, self._dp(), self.k
        obs = dict(stage=self.stage, point=k, t=float(dp.t[k]), t_since_open=float(dp.t[k] - c.t_open),
                   signal=float(dp.signal[k]), group=c.group, **c.attributes, last_point=k == len(dp) - 1)
        if self.stage == 2:
            t1 = float(self.cache.dp1.t[self.k1])
            obs["t_since_first"] = float(dp.t[k] - t1)
            if k == 0:      # readings between intervention 1 and the first stage-2 point
                m = (c.times > t1) & (c.times < dp.t[0])
                obs["readings_since_first"] = list(zip(c.times[m].tolist(),
                                                       self.cache.signal2[self.k1][m].tolist()))
        return obs

    def step(self, action):
        dp = self._dp()
        if action == 1 or self.k == len(dp) - 1:
            if self.stage == 1:
                self.k1, self.stage, self.k = self.k, 2, 0
                return self._obs(), 0.0, False, {"acted_first_at": self.k1}
            k1, k2 = self.k1, self.k
            b1, b2, vbest = best_path(self.kpi)
            reward = float(self.kpi[k1][k2] + self.noise)
            info = dict(first_at=k1, second_at=k2, t_first=float(self.cache.dp1.t[k1]), t_second=float(dp.t[k2]),
                        expected_y=float(self.kpi[k1][k2]), best_expected_y=vbest,
                        best_second_given_first=float(np.max(self.kpi[k1])),
                        regret=vbest - float(self.kpi[k1][k2]))
            return None, reward, True, info
        self.k += 1
        return self._obs(), 0.0, False, {}
