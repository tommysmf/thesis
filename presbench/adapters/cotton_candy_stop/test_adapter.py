"""Tests specific to the cotton candy stop adapter (the core tests live in tests/test_core.py).

    python adapters/cotton_candy_stop/test_adapter.py ../datasets/cotton-candy/processed
"""
import os
import sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from adapters import get_adapter  # noqa: E402
from adapters.cotton_candy_stop.adapter import seconds_above, START_ACTIVITY  # noqa: E402
from adapters.cotton_candy.adapter import energy_used  # noqa: E402
from presbench import make_settings  # noqa: E402

DATA = os.environ.get("PRESBENCH_DATA") or (sys.argv[1] if len(sys.argv) > 1 else None)
A = get_adapter("cotton_candy_stop")
_cache = {}


def cases():
    if "cases" not in _cache:
        _cache["cases"] = A.load(DATA, verbose=False)
    return _cache["cases"]


def test_window_is_the_real_spinning_phase():
    """The window opens at the real start and closes at the real stop, so replaying the signal is valid."""
    for c in cases():
        assert c.t_open == c.info["t_real_start"] and c.t_close == c.info["t_real_end"]
        assert c.t_close - c.t_open >= 20


def test_events_show_the_start_but_not_the_cooking_time():
    for c in cases():
        acts = set(c.events.activity)
        assert START_ACTIVITY in acts and not any("cooking time" in a for a in acts)
        assert c.events.t.max() <= c.t_open + 1e-9
        assert float(c.events.loc[c.events.activity == START_ACTIVITY, "t"].iloc[0]) == c.t_open


def test_policy_is_a_timer_from_the_same_batch():
    params = make_settings(A).params
    pol = A.policy(cases(), params)
    spins = {}
    for c in cases():
        spins.setdefault(c.group, set()).add(c.info["real_spin"])
    for c in cases():
        p = pol.pools[c.case_id]
        assert pol.kinds[c.case_id] == "delay" and 0 < len(p) <= params.pool_size
        assert c.info["real_spin"] in p and set(p) <= spins[c.group]


def test_seconds_above_matches_a_direct_count():
    for c in cases()[:20]:
        dp = c.decision_points()
        level = float(np.median(dp.signal))
        got = seconds_above(c, dp.t, level)
        for j in [0, len(dp) // 2, len(dp) - 1]:
            # piecewise constant: each interval takes the last reading at or before its start
            cuts = np.concatenate([[c.t_open], c.times[(c.times > c.t_open) & (c.times < dp.t[j])], [dp.t[j]]])
            last = np.searchsorted(c.times, cuts[:-1], side="right") - 1
            want = float(np.sum(np.diff(cuts) * (c.signal[last] > level)))
            assert abs(got[j] - want) < 1e-6, (c.case_id, j, got[j], want)


def test_outcome_shape_and_kpi():
    """Weight builds up with spin time, the cold penalty applies below T_cold, and the KPI subtracts the costs."""
    s = make_settings(A)
    p, out = s.params, A.outcome(s.params)
    for c in cases():
        dp = c.decision_points()
        w, kpi = out.expected(c, dp, 0.0)
        cold = p.cold_slope * np.maximum(0, p.T_cold - dp.signal)
        assert np.allclose(w, np.maximum(p.W_max * (1 - np.exp(-dp.t_rel / p.tau)) - cold, 0))
        cost = p.energy_price * energy_used(c, dp.t) + p.stress_price * seconds_above(c, dp.t, p.T_stress)
        assert np.allclose(kpi, w - cost)


def test_number_of_usable_runs():
    assert len(cases()) == 167


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)
    print(f"all {len(tests)} cotton candy stop adapter tests passed")
