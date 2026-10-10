"""Consistency tests for the generator.  Run:  python tests/test_generator.py <path to processed>
(or with pytest, setting the environment variable CC_PROCESSED to that path)."""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ccgen import Config, load_curves, generate, CottonCandyEnv  # noqa: E402
from ccgen.generator import case_states, policy_pools, build_case  # noqa: E402

PROCESSED = os.environ.get("CC_PROCESSED") or (sys.argv[1] if len(sys.argv) > 1 else None)
_cache = {}


def setup():
    if "tabs" not in _cache:
        curves = load_curves(PROCESSED, verbose=False)
        cfg = Config(resamples_per_curve=5)
        cases, tabs = generate(curves, cfg)
        _cache.update(curves=curves, cfg=cfg, cases=cases, tabs=tabs)
    return _cache["curves"], _cache["cfg"], _cache["cases"], _cache["tabs"]


def test_spin_start_follows_the_batch_rule():
    """Batches 0-14: spin start = create_calling + wait_time; batches 15-23: create_calling."""
    curves, _, _, _ = setup()
    runs = pd.read_csv(os.path.join(PROCESSED, "runs.csv"))
    for col in ["create_calling", "machine_on_done"]:
        runs[col] = pd.to_datetime(runs[col], utc=True, format="ISO8601")
    r = runs.set_index("instance")
    for c in curves:
        batch_no = int("".join(ch for ch in c.batch if ch.isdigit()))
        assert c.real_controller == (batch_no >= 15)
        create = (r.loc[c.curve_id, "create_calling"] - r.loc[c.curve_id, "machine_on_done"]).total_seconds()
        expect = create if c.real_controller else create + max(r.loc[c.curve_id, "wait_time"], 0)
        assert abs(c.t_real_start - expect) < 1e-6


def test_policy_pools_use_comparable_real_runs():
    curves, cfg, _, _ = setup()
    pools = policy_pools(curves, cfg)
    for c in curves:
        p = pools[c.curve_id]
        assert 0 < len(p) <= cfg.pool_size
        if c.real_controller:
            assert 45 < np.median(p) < 75
        elif c.cold:
            assert np.median(p) > 50          # cold machines waited long
        else:
            assert c.real_wait in p           # the run's own setting is among its nearest neighbours


def test_propensity_sums_to_one_and_ignores_hidden_draws():
    """p_start_here may only depend on what a method can see: resamples of one curve (same readings) must
    get identical propensities, whatever setting or hidden factor each case drew."""
    curves, _, _, tabs = setup()
    assert np.allclose(tabs["answer_key"].groupby("case_id").p_start_here.sum(), 1)
    subset = [c for c in curves if c.real_controller][:2] + [c for c in curves if not c.real_controller][:2]
    _, t2 = generate(subset, Config(resamples_per_curve=3, hidden_policy=3.0, hidden_effect=3.0))
    key = t2["answer_key"].assign(curve=lambda d: d.case_id.str.split("-").str[0])
    for _, g in key.groupby("curve"):
        arrays = [x.p_start_here.to_numpy() for _, x in g.groupby("case_id")]
        assert all(np.allclose(arrays[0], a) for a in arrays[1:])


def test_sampling_matches_propensity():
    """Over many draws for one curve, the share of starts at each point matches p_start_here,
    also when a hidden factor moves the controller threshold."""
    curves, _, _, _ = setup()
    picks = [next(c for c in curves if c.real_controller), next(c for c in curves if not c.real_controller)]
    for cfg in [Config(delta=0.7), Config(delta=0.7, hidden_policy=5.0)]:
        pools = policy_pools(curves, cfg)
        rng = np.random.default_rng(1)
        for c in picks:
            draws = [build_case(c, 0, cfg, rng, "train", pools) for _ in range(4000)]
            n = len(draws[0]["st"]["t"])
            counts = np.bincount([d["k_start"] for d in draws], minlength=n) / len(draws)
            assert np.abs(counts - draws[0]["pi"]).sum() / 2 < 0.04      # total variation distance


def test_decision_points_are_real_readings():
    _, _, cases, _ = setup()
    for cs in cases[:50]:
        assert np.isin(cs["st"]["t"], cs["curve"].x).all()
        assert cs["st"]["t"][0] >= cs["curve"].t_ready and cs["st"]["t"][-1] <= cs["curve"].t_end


def test_no_curve_in_both_splits():
    _, _, _, tabs = setup()
    assert (tabs["cases"].groupby("curve_id").split.nunique() == 1).all()


def test_observed_tables_hide_the_truth():
    _, _, _, tabs = setup()
    hidden = {"h_opt", "expected_y", "expected_weight", "y_if_start", "p_start_here", "is_best", "regret",
              "noise", "arm", "setting", "hidden", "n_points"}
    for name in ["event_log", "sensor_stream", "decision_points", "cases"]:
        assert not hidden & set(tabs[name].columns), name


def test_observed_outcome_equals_answer_key_at_start():
    _, cfg, _, tabs = setup()
    key = tabs["answer_key"].merge(tabs["cases"][["case_id", "start_point", "y", "weight", "t_ready"]], on="case_id")
    at = key[key.point == key.start_point]
    assert np.allclose(at.y_if_start, at.y)
    assert np.allclose(at.weight - at.y, cfg.lam * (at.t - at.t_ready))


def test_observed_reading_matches_sensor_stream():
    _, _, _, tabs = setup()
    m = tabs["decision_points"].merge(tabs["sensor_stream"], on=["case_id", "t"])
    assert len(m) == len(tabs["decision_points"]) and np.allclose(m["head"], m["ir_head"])


def test_decision_points_and_stream_stop_at_start():
    _, _, _, tabs = setup()
    dp = tabs["decision_points"]
    assert (dp.groupby("case_id").started.sum() == 1).all()
    assert (dp.sort_values("point").groupby("case_id").tail(1).started == 1).all()
    end = tabs["sensor_stream"].groupby("case_id").t.max()
    start = tabs["cases"].set_index("case_id").t_start
    assert (end <= start.loc[end.index] + 1e-9).all()


def test_online_mode_matches_generator():
    curves, cfg, _, _ = setup()
    env = CottonCandyEnv(curves, Config(), split="test")
    for i in range(5):
        obs = env.reset(curve_index=i)
        st = case_states(env.curve)
        assert np.isclose(obs["head"], st["head"][0])
        k = 0
        while True:
            obs, reward, done, info = env.step(1 if k == 7 else 0)
            if done:
                break
            k += 1
        assert info["started_at"] == min(7, len(st["t"]) - 1)
        assert info["regret"] >= -1e-9


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)
    print(f"all {len(tests)} tests passed")
