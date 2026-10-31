"""Online mode (like SimBank's): step through a case and let a policy decide when to intervene.

    env = OnlineEnv(adapter, cases, settings, split="test")
    obs = env.reset()                     # obs["history"]: signal readings before the window opened
    while True:
        action = 1 if obs["signal"] >= 62 else 0          # your policy: 1 = intervene now, 0 = wait
        obs, reward, done, info = env.step(action)
        if done: break
    # reward = the KPI of this case; info["regret"] = how much better the best decision point was

Each new signal reading inside the window is a decision point; the last one intervenes automatically.
"""
import numpy as np

from .generator import split_cases, draw_case


class OnlineEnv:
    def __init__(self, adapter, cases, settings, split="test", seed=None):
        splits = split_cases(cases, settings)
        self.cases = [c for c in cases if split is None or splits[c.case_id] == split]
        self.adapter, self.settings = adapter, settings
        self.outcome = adapter.outcome(settings.params)
        self.rng = np.random.default_rng(settings.seed + 2 if seed is None else seed)

    def reset(self, case_index=None):
        if case_index is None:
            case_index = int(self.rng.integers(len(self.cases)))
        self.case = c = self.cases[case_index]
        d = draw_case(self.settings, self.rng)
        self.dp = c.decision_points()
        self.kpi = self.outcome.expected(c, self.dp, d["hidden"])[1]
        self.noise = d["noise"]
        self.k = 0
        obs = self._obs()
        before = c.times < self.dp.t[0]
        obs["history"] = list(zip(c.times[before].tolist(), c.signal[before].tolist()))
        return obs

    def _obs(self):
        c, k, dp = self.case, self.k, self.dp
        return dict(point=k, t=float(dp.t[k]), t_since_open=float(dp.t_rel[k]), signal=float(dp.signal[k]),
                    group=c.group, **c.attributes, last_point=k == len(dp) - 1)

    def step(self, action):
        if action == 1 or self.k == len(self.dp) - 1:
            reward = float(self.kpi[self.k] + self.noise)
            info = dict(started_at=self.k, t_start=float(self.dp.t[self.k]), expected_y=float(self.kpi[self.k]),
                        best_expected_y=float(self.kpi.max()), regret=float(self.kpi.max() - self.kpi[self.k]))
            return None, reward, True, info
        self.k += 1
        return self._obs(), 0.0, False, {}
