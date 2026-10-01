"""Online mode (like SimBank's): step through a case and let a policy decide when to start.

    env = CottonCandyEnv(curves, cfg, split="test")
    obs = env.reset()
    while True:
        action = 1 if obs["head"] >= 62 else 0          # your policy: 1 = start spinning now, 0 = wait
        obs, reward, done, info = env.step(action)
        if done: break
    # reward = the KPI (g) of this case; info["regret"] = how much better the best moment was

The case at the last decision point starts automatically.
"""
import numpy as np

from .generator import split_curves, case_states
from .mechanisms import optimal_head, expected_outcome


class CottonCandyEnv:
    def __init__(self, curves, cfg, split="test", seed=None):
        splits = split_curves(curves, cfg)
        self.curves = [c for c in curves if split is None or splits[c.curve_id] == split]
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed + 2 if seed is None else seed)

    def reset(self, curve_index=None):
        if curve_index is None:
            curve_index = int(self.rng.integers(len(self.curves)))
        cfg = self.cfg
        self.curve = c = self.curves[curve_index]
        stretch = 1.0 + (self.rng.uniform(-cfg.curve_stretch, cfg.curve_stretch) if cfg.curve_stretch > 0 else 0.0)
        self.t, self.head, self.slope = case_states(c, cfg, stretch)
        self.ey = expected_outcome(self.head, self.t, optimal_head(c.wear, c.hum_z, cfg), cfg)
        self.noise = self.rng.normal(0.0, cfg.noise_sd)
        self.k = 0
        return self._obs()

    def _obs(self):
        c, k = self.curve, self.k
        return dict(point=k, t=float(self.t[k]), head=float(self.head[k]), head_slope=float(self.slope[k]),
                    env_temp=c.env_temp, env_hum=c.env_hum, wear=c.wear, last_point=k == len(self.t) - 1)

    def step(self, action):
        if action == 1 or self.k == len(self.t) - 1:
            reward = float(self.ey[self.k] + self.noise)
            info = dict(started_at=self.k, t_start=float(self.t[self.k]), expected_y=float(self.ey[self.k]),
                        best_expected_y=float(self.ey.max()), regret=float(self.ey.max() - self.ey[self.k]))
            return None, reward, True, info
        self.k += 1
        return self._obs(), 0.0, False, {}
