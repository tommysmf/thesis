"""Consistency tests for the generator.  Run:  python tests/test_generator.py <path to processed>
(or with pytest, setting the environment variable CC_PROCESSED to that path)."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ccgen import Config, load_curves, generate, CottonCandyEnv  # noqa: E402
from ccgen.mechanisms import start_probability, start_distribution, historical_start  # noqa: E402
from ccgen.generator import case_states  # noqa: E402

PROCESSED = os.environ.get("CC_PROCESSED") or (sys.argv[1] if len(sys.argv) > 1 else None)
_cache = {}


def setup():
    if "tabs" not in _cache:
        curves = load_curves(PROCESSED, verbose=False)
        cfg = Config(resamples_per_curve=10)
        _, tabs = generate(curves, cfg)
        _cache.update(curves=curves, cfg=cfg, tabs=tabs)
    return _cache["curves"], _cache["cfg"], _cache["tabs"]


def test_start_distribution_sums_to_one():
    cfg = Config()
    for delta in (0.0, 0.5, 1.0):
        p = start_probability(np.linspace(40, 90, 50), np.linspace(19, 120, 50), cfg)
        assert abs(start_distribution(p, delta).sum() - 1) < 1e-9


def test_sampling_matches_exact_distribution():
    cfg = Config(delta=0.7)
    p = start_probability(np.linspace(45, 80, 30), np.linspace(19, 80, 30), cfg)
    rng = np.random.default_rng(0)
    counts = np.bincount([historical_start(p, cfg, rng)[0] for _ in range(40000)], minlength=len(p)) / 40000
    assert np.abs(counts - start_distribution(p, cfg.delta)).max() < 0.01


def test_no_curve_in_both_splits():
    _, _, tabs = setup()
    per_curve = tabs["cases"].groupby("curve_id").split.nunique()
    assert (per_curve == 1).all()


def test_observed_tables_hide_the_truth():
    _, _, tabs = setup()
    hidden = {"h_opt", "expected_y", "y_if_start", "p_start_hazard", "p_start_here", "is_best", "regret", "noise"}
    for name in ["event_log", "sensor_stream", "decision_points", "cases"]:
        assert not hidden & set(tabs[name].columns), name


def test_observed_y_equals_answer_key_at_start():
    _, _, tabs = setup()
    key = tabs["answer_key"].merge(tabs["cases"][["case_id", "start_point", "y"]], on="case_id")
    at = key[key.point == key.start_point]
    assert np.allclose(at.y_if_start, at.y)


def test_decision_points_stop_at_start():
    _, _, tabs = setup()
    dp = tabs["decision_points"]
    assert (dp.groupby("case_id").started.sum() == 1).all()
    last = dp.sort_values("point").groupby("case_id").tail(1)
    assert (last.started == 1).all()


def test_sensor_stream_ends_at_start():
    _, _, tabs = setup()
    end = tabs["sensor_stream"].groupby("case_id").t.max()
    start = tabs["cases"].set_index("case_id").t_start
    assert (end <= start.loc[end.index] + 1e-9).all()


def test_online_mode_matches_generator():
    curves, cfg, _ = setup()
    env = CottonCandyEnv(curves, cfg, split="test")
    for i in range(5):
        obs = env.reset(curve_index=i)
        t, head, _ = case_states(env.curve, cfg)
        assert np.isclose(obs["head"], head[0])
        k = 0
        while True:
            obs, reward, done, info = env.step(1 if k == 7 else 0)
            if done:
                break
            k += 1
        assert info["started_at"] == min(7, len(t) - 1)
        assert info["regret"] >= -1e-9


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)
    print(f"all {len(tests)} tests passed")
