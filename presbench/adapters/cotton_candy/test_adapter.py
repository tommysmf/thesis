"""Tests specific to the cotton candy adapter (the core tests live in tests/test_core.py).

    python adapters/cotton_candy/test_adapter.py ../datasets/cotton-candy/processed
"""
import os
import sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from adapters import get_adapter  # noqa: E402
from presbench import make_settings  # noqa: E402

DATA = os.environ.get("PRESBENCH_DATA") or (sys.argv[1] if len(sys.argv) > 1 else None)
A = get_adapter("cotton_candy")
_cache = {}


def cases():
    if "cases" not in _cache:
        _cache["cases"] = A.load(DATA, verbose=False)
    return _cache["cases"]


def test_spin_start_follows_the_batch_rule():
    """Batches 0-14: spin start = create_calling + wait_time; batches 15-23: create_calling."""
    runs = pd.read_csv(os.path.join(DATA, "runs.csv"))
    for col in ["create_calling", "machine_on_done"]:
        runs[col] = pd.to_datetime(runs[col], utc=True, format="ISO8601")
    r = runs.set_index("instance")
    for c in cases():
        rid = int(c.case_id)
        batch_no = int("".join(ch for ch in c.group if ch.isdigit()))
        assert c.info["real_controller"] == (batch_no >= 15)
        create = (r.loc[rid, "create_calling"] - r.loc[rid, "machine_on_done"]).total_seconds()
        expect = create if c.info["real_controller"] else create + max(r.loc[rid, "wait_time"], 0)
        assert abs(c.info["t_real_start"] - expect) < 1e-6


def test_policy_pools_use_comparable_real_runs():
    params = make_settings(A).params
    pol = A.policy(cases(), params)
    for c in cases():
        p = pol.pools[c.case_id]
        assert 0 < len(p) <= params.pool_size
        if c.info["real_controller"]:
            assert pol.kinds[c.case_id] == "threshold" and 45 < np.median(p) < 75
        elif c.info["cold"]:
            assert pol.kinds[c.case_id] == "delay" and np.median(p) > 50     # cold machines waited long
        else:
            assert c.info["real_wait"] in p        # the run's own setting is among its nearest neighbours


def test_energy_cost_follows_the_real_power_trace():
    """Energy from t_open grows like the real power draw (~970 W), and the energy KPI is the weight minus it."""
    from adapters.cotton_candy.adapter import energy_used
    settings = make_settings(A, "energy")
    outcome = A.outcome(settings.params)
    for c in cases():
        dp = c.decision_points()
        e = energy_used(c, dp.t)
        assert 0 <= e[0] <= 1050 * (dp.t[0] - c.t_open) / 3600 + 1e-9 and np.all(np.diff(e) > 0)
        watts = (e[-1] - e[0]) * 3600 / (dp.t[-1] - dp.t[0])
        assert 800 < watts < 1050, (c.case_id, watts)
        measure, kpi = outcome.expected(c, dp, 0.0)
        assert np.allclose(kpi, measure - settings.energy_price * e)


def test_default_kpi_has_no_energy_cost():
    """The default settings keep the time cost only (same output as before the energy scenario existed)."""
    params = make_settings(A).params
    c = cases()[0]
    dp = c.decision_points()
    measure, kpi = A.outcome(params).expected(c, dp, 0.0)
    assert params.energy_price == 0 and np.allclose(kpi, measure - params.lam * dp.t_rel)


def heating():
    if "heating" not in _cache:
        from adapters.cotton_candy.heating import fit_heating
        _cache["heating"] = fit_heating(cases())
    return _cache["heating"]


def test_heating_trajectory_keeps_the_real_readings_where_valid():
    """The real start reproduces the real run up to the real stop; any other start keeps the real readings
    before the earlier of the two starts; the simulated head is finite, continuous at the start and plausible."""
    from adapters.cotton_candy.heating import trajectory
    for c in cases():
        h, a, b = heating()[c.case_id], c.info["t_real_start"], c.info["t_real_end"]
        real = trajectory(c, h, a)
        assert np.allclose(real[c.times <= b], c.signal[c.times <= b])
        for s in np.linspace(c.t_open, c.t_close, 5):
            T = trajectory(c, h, s)
            keep = c.times <= min(s, a)
            assert np.allclose(T[keep], c.signal[keep])
            assert np.all(np.isfinite(T)) and T.max() < 170
            nxt = np.searchsorted(c.times, s, side="right")
            if 0 < nxt < len(c.times) and c.times[nxt] - s < 7:   # first simulated reading near the head at s
                assert abs(T[nxt] - np.interp(s, c.times, T)) < 6, (c.case_id, s)


def test_heating_waiting_after_the_real_start_follows_the_waiting_slope():
    from adapters.cotton_candy.heating import trajectory
    for c in cases():
        h, a = heating()[c.case_id], c.info["t_real_start"]
        s = a + 30
        T = trajectory(c, h, s, noise=False)
        m = (c.times > a) & (c.times <= s)
        if m.sum() >= 2:
            slope = np.polyfit(c.times[m], T[m], 1)[0]
            assert abs(slope - h.wait.slope) < 1e-6


def test_number_of_usable_runs():
    assert len(cases()) == 171


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)
    print(f"all {len(tests)} cotton candy adapter tests passed")
