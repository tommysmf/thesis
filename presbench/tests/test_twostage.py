"""Core tests for two linked decisions (presbench/twostage.py), whatever the adapter.

    python tests/test_twostage.py                                              # on the synthetic toy adapter
    python tests/test_twostage.py <two-stage adapter> <data path>              # on a real adapter
(or with pytest, setting PRESBENCH_ADAPTER and PRESBENCH_DATA). Run these for every new two-stage adapter.
"""
import os
import sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
from presbench import make_settings  # noqa: E402
from presbench import twostage as ts  # noqa: E402
from presbench.generator import split_cases  # noqa: E402

ADAPTER_NAME = os.environ.get("PRESBENCH_ADAPTER") or (sys.argv[1] if len(sys.argv) > 1 else "toy_twostage")
DATA = os.environ.get("PRESBENCH_DATA") or (sys.argv[2] if len(sys.argv) > 2 else None)
_cache = {}


def setup():
    if not _cache:
        if ADAPTER_NAME == "toy_twostage":
            import toy_twostage
            A = toy_twostage.ADAPTER
        else:
            from adapters import get_adapter
            A = get_adapter(ADAPTER_NAME)
        cases = A.load(DATA, verbose=False)
        settings = make_settings(A, resamples_per_case=3)
        generated, tabs = ts.generate(A, cases, settings)
        _cache.update(A=A, cases=cases, settings=settings, generated=generated, tabs=tabs)
    return _cache


def test_cases_and_second_windows_are_valid():
    s = setup()
    for c in s["cases"]:
        assert np.all(np.diff(c.times) > 0) and len(c.times) == len(c.signal)
        assert len(c.decision_points()) >= 2 and (c.events.t <= c.t_open + 1e-9).all()
        for t1 in c.decision_points().t[:: max(1, len(c.decision_points()) // 5)]:
            lo, hi = s["A"].second_window(c, float(t1))
            assert t1 < lo <= hi
            sig = s["A"].signal_after(c, float(t1))
            assert np.allclose(sig[c.times <= t1], c.signal[c.times <= t1]), "nothing changes before intervention 1"


def test_no_real_case_in_both_splits():
    s = setup()
    assert (s["tabs"]["cases"].groupby("real_case_id").split.nunique() == 1).all()


def test_observed_tables_hide_the_truth():
    s = setup()
    hidden = {"expected_y", "y_if_path", "p_path", "p_first", "is_best", "regret", "noise", "arm1", "arm2",
              "setting1", "setting2", "hidden", f"expected_{s['A'].outcome_name}"}
    for name in ["event_log", "sensor_stream", "decision_points", "cases"]:
        assert not hidden & set(s["tabs"][name].columns), name


def test_propensities_sum_to_one():
    s = setup()
    key, first = s["tabs"]["answer_key"], s["tabs"]["answer_key_first"]
    assert np.allclose(key.groupby("case_id").p_path.sum(), 1)
    assert np.allclose(first.groupby("case_id").p_first.sum(), 1)
    second = key.merge(first[["case_id", "point1", "p_first"]], on=["case_id", "point1"])
    assert np.allclose((second.p_path / second.p_first).groupby([second.case_id, second.point1]).sum(), 1)


def test_sampling_matches_propensity():
    """Over many draws for one real case, the share of paths (k1, k2) matches P(path), also when the hidden
    factor moves the stage-1 policy (if the adapter has a scenario with hidden_policy)."""
    s = setup()
    A, cases = s["A"], s["cases"]
    configs = [make_settings(A, delta=0.7)]
    configs += [make_settings(A, name, delta=0.7) for name, kw in A.scenarios.items() if kw.get("hidden_policy")]
    for st in configs:
        policies, outcome = A.policy(cases, st.params), A.outcome(st.params)
        rng = np.random.default_rng(1)
        for c in cases[:2]:
            cache = ts.RealCaseCache(A, c, st, *policies)
            n = 4000
            draws = [ts.build_case(c, 0, st, rng, "train", policies, outcome, cache) for _ in range(n)]
            p = np.concatenate([cache.pi1[j] * cache.dist2[j] for j in range(len(cache.dp1))])
            offs = np.cumsum([0] + [len(cache.dp2[j]) for j in range(len(cache.dp1))])
            counts = np.bincount([offs[d["k1"]] + d["k2"] for d in draws], minlength=len(p)) / n
            tol = 3 * 0.5 * np.sum(np.sqrt(p * (1 - p) / n)) + 0.01
            assert np.abs(counts - p).sum() / 2 < tol, (c.case_id, np.abs(counts - p).sum() / 2, tol)


def test_propensity_uses_only_observables():
    s = setup()
    A = s["A"]
    name = next((n for n, kw in A.scenarios.items() if kw.get("hidden_policy")), None)
    st = make_settings(A, name, resamples_per_case=4) if name else make_settings(A, resamples_per_case=4)
    _, tabs = ts.generate(A, s["cases"][:5], st)
    key = tabs["answer_key"].assign(real=lambda d: d.case_id.str.rsplit("-", n=1).str[0])
    for _, g in key.groupby("real"):
        arrays = [x.p_path.to_numpy() for _, x in g.groupby("case_id")]
        assert all(np.allclose(arrays[0], a) for a in arrays[1:])


def test_observed_outcome_equals_answer_key():
    s = setup()
    key = s["tabs"]["answer_key"].merge(s["tabs"]["cases"][["case_id", "first_point", "second_point", "y"]],
                                        on="case_id")
    at = key[(key.point1 == key.first_point) & (key.point2 == key.second_point)]
    assert len(at) == len(s["tabs"]["cases"]) and np.allclose(at.y_if_path, at.y)


def test_decision_points_follow_the_signal_and_stop_at_each_intervention():
    s = setup()
    sig, tabs = s["A"].signal_name, s["tabs"]
    dp = tabs["decision_points"]
    assert (dp.groupby(["case_id", "stage"]).acted.sum() == 1).all()
    assert (dp.sort_values("point").groupby(["case_id", "stage"]).tail(1).acted == 1).all()
    m = dp.merge(tabs["sensor_stream"], on=["case_id", "t"], suffixes=("", "_stream"))
    assert len(m) == len(dp) and np.allclose(m[sig], m[sig + "_stream"])
    c = tabs["cases"].set_index("case_id")
    end = tabs["sensor_stream"].groupby("case_id").t.max()
    assert (end <= c.t_second.loc[end.index] + 1e-9).all()
    assert (c.t_first < c.t_second).all()
    for g in s["generated"][:20]:          # the stream is the real signal up to intervention 1
        case = g["case"]
        st = tabs["sensor_stream"][tabs["sensor_stream"].case_id == g["case_id"]]
        real = np.interp(st.t, case.times, case.signal)
        before = st.t.to_numpy() <= g["cache"].dp1.t[g["k1"]]
        assert np.allclose(st[sig].to_numpy()[before], real[before])


def test_best_path_is_at_least_every_other_path():
    s = setup()
    key = s["tabs"]["answer_key"]
    best = key[key.is_best == 1].set_index("case_id").expected_y
    top = key.groupby("case_id").expected_y.max()
    assert best.index.is_unique and len(best) == len(top)
    assert (best.sort_index() >= top.sort_index() - 1e-9).all()
    t = s["tabs"]["case_truth"].set_index("case_id")
    assert (t.regret >= -1e-9).all() and (t.expected_y_best >= t.expected_y_best_second_given_first - 1e-9).all()


def test_online_mode_matches_generator():
    s = setup()
    A, st = s["A"], s["settings"]
    env = ts.TwoStageOnlineEnv(A, s["cases"], st, split="test")
    splits = split_cases(s["cases"], st)
    assert all(splits[c.case_id] == "test" for c in env.cases)
    for i in range(min(4, len(env.cases))):
        obs = env.reset(case_index=i)
        cache = env.cache
        assert obs["stage"] == 1 and np.isclose(obs["signal"], cache.dp1.signal[0])
        k = 0
        while obs["stage"] == 1:
            obs, _, _, info = env.step(1 if k == 2 else 0)
            k += 1
        k1 = info["acted_first_at"]
        assert k1 == min(2, len(cache.dp1) - 1) and np.isclose(obs["signal"], cache.dp2[k1].signal[0])
        k = 0
        while True:
            obs, reward, done, info = env.step(1 if k == 3 else 0)
            if done:
                break
            k += 1
        assert info["first_at"] == k1 and info["second_at"] == min(3, len(cache.dp2[k1]) - 1)
        assert info["regret"] >= -1e-9 and np.isclose(reward - env.noise, info["expected_y"])


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)
    print(f"all {len(tests)} two-stage core tests passed on adapter '{ADAPTER_NAME}'")
