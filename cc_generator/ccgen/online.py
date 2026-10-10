"""Online mode (like SimBank's): step through a case and let a policy decide when to start.

    env = CottonCandyEnv(curves, cfg, split="test")
    obs = env.reset()                     # obs["history"]: readings before the stick was placed
    while True:
        action = 1 if obs["head"] >= 62 else 0          # your policy: 1 = start spinning now, 0 = wait
        obs, reward, done, info = env.step(action)
        if done: break
    # reward = the KPI of this case; info["regret"] = how much better the best moment was

A decision point is each new (irregular) head reading after the stick is placed; the case starts
automatically at the last one.
"""
import numpy as np

from .generator import split_curves, case_states, draw_case
from .mechanisms import optimal_head, expected_kpi


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
        d = draw_case(c, cfg, self.rng)
        self.st = case_states(c)
        self.ey = expected_kpi(self.st["head"], self.st["t_rel"], optimal_head(c.wear, c.hum_z, cfg, d["hidden"]), cfg)
        self.noise = d["noise"]
        self.k = 0
        obs = self._obs()
        before = c.x < self.st["t"][0]
        obs["history"] = list(zip(c.x[before].tolist(), c.head[before].tolist()))
        return obs

    def _obs(self):
        c, k, st = self.curve, self.k, self.st
        return dict(point=k, t=float(st["t"][k]), t_since_ready=float(st["t_rel"][k]), head=float(st["head"][k]),
                    batch=c.batch, env_temp=c.env_temp, env_hum=c.env_hum, wear=c.wear,
                    last_point=k == len(st["t"]) - 1)

    def step(self, action):
        if action == 1 or self.k == len(self.st["t"]) - 1:
            reward = float(self.ey[self.k] + self.noise)
            info = dict(started_at=self.k, t_start=float(self.st["t"][self.k]), expected_y=float(self.ey[self.k]),
                        best_expected_y=float(self.ey.max()), regret=float(self.ey.max() - self.ey[self.k]))
            return None, reward, True, info
        self.k += 1
        return self._obs(), 0.0, False, {}
