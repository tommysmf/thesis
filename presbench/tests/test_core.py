"""Core tests: properties every generated benchmark must have, whatever the adapter.

    python tests/test_core.py                                         # on the synthetic toy adapter (no data needed)
    python tests/test_core.py cotton_candy ../datasets/cotton-candy/processed   # on a real adapter
(or with pytest, setting PRESBENCH_ADAPTER and PRESBENCH_DATA). Run these for every new adapter.
"""
import os
import sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
from presbench import make_settings, generate, OnlineEnv  # noqa: E402
from presbench.generator import build_case, split_cases  # noqa: E402

ADAPTER_NAME = os.environ.get("PRESBENCH_ADAPTER") or (sys.argv[1] if len(sys.argv) > 1 else "toy")
# "toy" and "toy_falling" are the synthetic adapters in tests/toy_adapter.py (rising and falling signal)
DATA = os.environ.get("PRESBENCH_DATA") or (sys.argv[2] if len(sys.argv) > 2 else None)
_cache = {}


def setup():
    if not _cache:
        if ADAPTER_NAME in ("toy", "toy_falling"):
            import toy_adapter
            A = toy_adapter.ADAPTER if ADAPTER_NAME == "toy" else toy_adapter.FALLING
        else:
            from adapters import get_adapter
            A = get_adapter(ADAPTER_NAME)
        cases = A.load(DATA, verbose=False)
        settings = make_settings(A, resamples_per_case=5)
        generated, tabs = generate(A, cases, settings)
        _cache.update(A=A, cases=cases, settings=settings, generated=generated, tabs=tabs)
    return _cache


def test_cases_are_valid():
    s = setup()
    for c in s["cases"]:
        assert np.all(np.diff(c.times) > 0), "signal times must be strictly increasing"
        assert len(c.times) == len(c.signal)
        assert len(c.decision_points()) >= 2, "a window needs at least two decision points"
        assert c.t_open <= c.t_close
        assert (c.events.t <= c.t_open + 1e-9).all(), "logged real events must precede the window"


def test_no_real_case_in_both_splits():
    s = setup()
    assert (s["tabs"]["cases"].groupby("real_case_id").split.nunique() == 1).all()


def test_observed_tables_hide_the_truth():
    s = setup()
    hidden = {"expected_y", "y_if_start", "p_start_here", "is_best", "regret", "noise", "arm", "setting", "hidden",
              f"expected_{s['A'].outcome_name}"}
    for name in ["event_log", "sensor_stream", "decision_points", "cases"]:
        assert not hidden & set(s["tabs"][name].columns), name


def test_propensities_sum_to_one():
    s = setup()
    assert np.allclose(s["tabs"]["answer_key"].groupby("case_id").p_start_here.sum(), 1)


def test_sampling_matches_propensity():
    """Over many draws for one real case, the share of decisions at each point matches p_start_here, also when
    the hidden factor moves the policy (if the adapter has a scenario with hidden_policy)."""
    s = setup()
    A, cases = s["A"], s["cases"]
    configs = [make_settings(A, delta=0.7)]
    configs += [make_settings(A, name, delta=0.7) for name, kw in A.scenarios.items() if kw.get("hidden_policy")]
    for st in configs:
        policy, outcome = A.policy(cases, st.params), A.outcome(st.params)
        rng = np.random.default_rng(1)
        for c in cases[:3]:
            draws = [build_case(c, 0, st, rng, "train", policy, outcome) for _ in range(3000)]
            n = len(draws[0]["dp"])
            counts = np.bincount([d["k"] for d in draws], minlength=n) / len(draws)
            pi = draws[0]["pi"]
            # total variation distance; pure sampling noise gives about 0.5 * sum(sqrt(p(1-p)/N) * 0.8),
            # so allow 3 times that (it grows with the number of decision points) plus a small margin
            tol = 3 * 0.5 * np.sum(np.sqrt(pi * (1 - pi) / len(draws))) + 0.01
            assert np.abs(counts - pi).sum() / 2 < tol, (c.case_id, np.abs(counts - pi).sum() / 2, tol)


def test_propensity_uses_only_observables():
    """Resamples of one real case must get identical propensities, whatever hidden draws they got."""
    s = setup()
    A = s["A"]
    name = next((n for n, kw in A.scenarios.items() if kw.get("hidden_policy")), None)
    st = make_settings(A, name, resamples_per_case=4) if name else make_settings(A, resamples_per_case=4)
    _, tabs = generate(A, s["cases"][:6], st)
    key = tabs["answer_key"].assign(real=lambda d: d.case_id.str.rsplit("-", n=1).str[0])
    for _, g in key.groupby("real"):
        arrays = [x.p_start_here.to_numpy() for _, x in g.groupby("case_id")]
        assert all(np.allclose(arrays[0], a) for a in arrays[1:])


def test_observed_outcome_equals_answer_key():
    s = setup()
    key = s["tabs"]["answer_key"].merge(s["tabs"]["cases"][["case_id", "start_point", "y"]], on="case_id")
    at = key[key.point == key.start_point]
    assert np.allclose(at.y_if_start, at.y)


def test_decision_points_are_real_readings_and_stop_at_start():
    s = setup()
    sig = s["A"].signal_name
    for g in s["generated"][:30]:
        assert np.isin(g["dp"].t, g["case"].times).all()
    dp = s["tabs"]["decision_points"]
    assert (dp.groupby("case_id").started.sum() == 1).all()
    assert (dp.sort_values("point").groupby("case_id").tail(1).started == 1).all()
    m = dp.merge(s["tabs"]["sensor_stream"], on=["case_id", "t"], suffixes=("", "_stream"))
    assert len(m) == len(dp) and np.allclose(m[sig], m[sig + "_stream"])
    end = s["tabs"]["sensor_stream"].groupby("case_id").t.max()
    assert (end <= s["tabs"]["cases"].set_index("case_id").t_start.loc[end.index] + 1e-9).all()


def test_online_mode_matches_generator():
    s = setup()
    env = OnlineEnv(s["A"], s["cases"], s["settings"], split="test")
    for i in range(min(5, len(env.cases))):
        obs = env.reset(case_index=i)
        dp = env.case.decision_points()
        assert np.isclose(obs["signal"], dp.signal[0])
        k = 0
        while True:
            obs, reward, done, info = env.step(1 if k == 3 else 0)
            if done:
                break
            k += 1
        assert info["started_at"] == min(3, len(dp) - 1) and info["regret"] >= -1e-9


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)
    print(f"all {len(tests)} core tests passed on adapter '{ADAPTER_NAME}'")
