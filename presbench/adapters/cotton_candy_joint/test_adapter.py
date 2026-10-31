"""Tests specific to the cotton candy joint adapter (the two-stage core tests live in tests/test_twostage.py).

    python adapters/cotton_candy_joint/test_adapter.py ../datasets/cotton-candy/processed
"""
import os
import sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from adapters import get_adapter  # noqa: E402
from adapters.cotton_candy_joint.adapter import MIN_SPIN, MAX_SPIN  # noqa: E402
from presbench import make_settings  # noqa: E402
from presbench.twostage import second_points  # noqa: E402

DATA = os.environ.get("PRESBENCH_DATA") or (sys.argv[1] if len(sys.argv) > 1 else None)
A = get_adapter("cotton_candy_joint")
_cache = {}


def cases():
    if "cases" not in _cache:
        _cache["cases"] = A.load(DATA, verbose=False)
    return _cache["cases"]


def test_stage_one_signal_is_the_head_as_if_still_waiting():
    """Real readings up to the real start; after it, the run's waiting line (not the real, spinning readings)."""
    for c in cases():
        real, a, fit = c.info["real"], c.info["t_real_start"], c.info["heating"]
        before = c.times <= a
        assert np.allclose(c.signal[before], real.signal[before])
        after = c.times > a
        if after.sum() >= 2:
            slope = np.polyfit(c.times[after], c.signal[after] - fit.wait.residual(c.times[after]), 1)[0]
            assert abs(slope - fit.wait.slope) < 1e-6


def test_real_start_reproduces_the_real_run():
    for c in cases():
        real, a, b = c.info["real"], c.info["t_real_start"], c.info["t_real_end"]
        sig = A.signal_after(c, a)
        assert np.allclose(sig[c.times <= b], real.signal[c.times <= b])


def test_stop_window_and_policy():
    params = make_settings(A).params
    start, stop = A.policy(cases(), params)
    for c in cases()[:40]:
        dp1 = c.decision_points()
        for t1 in dp1.t[:: max(1, len(dp1) // 4)]:
            lo, hi = A.second_window(c, float(t1))
            assert np.isclose(lo - t1, MIN_SPIN) and np.isclose(hi - t1, MAX_SPIN)
            assert len(second_points(c, A.signal_after(c, float(t1)), lo, hi)) >= 5
        spins = sorted(o.info["real_spin"] for o in cases() if o.group == c.group)
        assert all(any(np.isclose(p + MIN_SPIN, s) or p == 0 for s in spins) for p in stop.pools[c.case_id])
        assert stop.kinds[c.case_id] == "delay" and start.kinds[c.case_id] in ("threshold", "delay")


def test_outcome_formula():
    s = make_settings(A)
    p, out = s.params, A.outcome(s.params)
    c = cases()[0]
    dp1 = c.decision_points()
    k1 = len(dp1) // 2
    t1 = float(dp1.t[k1])
    sig = A.signal_after(c, t1)
    dp2 = second_points(c, sig, *A.second_window(c, t1))
    w, kpi = out.expected(c, dp1, k1, dp2, 0.0)
    h_opt = p.h0 + p.a_wear * (c.attributes["wear"] - 30) / 30
    bell = np.exp(-((dp1.signal[k1] - h_opt) / p.w) ** 2)
    want = np.maximum(p.W_max * bell * (1 - np.exp(-(dp2.t - t1) / p.tau))
                      - p.cold_slope * np.maximum(0, p.T_cold - dp2.signal), 0)
    assert np.allclose(w, want)
    j = len(dp2) - 1                                   # costs at the last stop point, counted directly
    grid = c.times[(c.times >= c.t_open) & (c.times <= dp2.t[j])]
    hot = sum(np.diff(c.times)[i] for i in range(len(c.times) - 1)
              if c.t_open <= c.times[i] and c.times[i + 1] <= dp2.t[j] and sig[i] > p.T_stress)
    first = np.searchsorted(c.times, c.t_open)          # the partial interval up to the first reading in the window
    if first > 0 and sig[first - 1] > p.T_stress and len(grid):
        hot += grid[0] - c.t_open
    energy = c.info["power_w"] * (dp2.t[j] - c.t_open) / 3600
    assert np.isclose(kpi[j], w[j] - p.energy_price * energy - p.stress_price * hot)
    assert 800 < c.info["power_w"] < 1050


def test_number_of_usable_runs():
    assert len(cases()) == 171


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)
    print(f"all {len(tests)} cotton candy joint adapter tests passed")
