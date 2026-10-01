"""The two specified mechanisms: the historical policy and the outcome.

Both are plain functions of the case state, so methods, baselines and the online mode all use
exactly the same definitions as the generator.
"""
import numpy as np


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


# ---- historical policy ------------------------------------------------------------------------
def start_probability(head, t, cfg):
    """Chance that the historical operator starts spinning at this decision point (if not yet started).

    p = sigmoid(beta*(head - h_star) + gamma*(t - t_star)), clipped to [eps, 1 - eps].
    """
    p = sigmoid(cfg.beta * (np.asarray(head) - cfg.h_star) + cfg.gamma * (np.asarray(t) - cfg.t_star))
    return np.clip(p, cfg.eps, 1 - cfg.eps)


def sample_start(p, rng):
    """Walk through the decision points; the first coin flip that says 'start' wins.
    The last point always starts (forced). Returns the index of the start point."""
    hits = rng.random(len(p)) < p
    return int(np.argmax(hits)) if hits.any() else len(p) - 1


def historical_start(p, cfg, rng):
    """Start index under the historical policy: with probability delta the rule (hazard p),
    otherwise a uniformly random decision point (randomized, unconfounded)."""
    if rng.random() < cfg.delta:
        return sample_start(p, rng), True
    return int(rng.integers(len(p))), False


def start_distribution(p, delta=1.0):
    """Exact probability of starting at each point under the historical policy:
    delta * p_k * prod_{j<k}(1 - p_j)  (the last point takes the rest)  +  (1 - delta) / K."""
    p = np.asarray(p, dtype=float).copy()
    p[-1] = 1.0
    survive = np.concatenate([[1.0], np.cumprod(1 - p[:-1])])
    return delta * p * survive + (1 - delta) / len(p)


# ---- outcome ----------------------------------------------------------------------------------
def optimal_head(wear, hum_z, cfg):
    """Case-specific optimal head temperature (degC)."""
    return cfg.h0 + cfg.a_wear * (wear - 30.0) / 30.0 + cfg.b_humidity * hum_z


def expected_outcome(head, t, h_opt, cfg):
    """Expected KPI (g) when spinning starts at head temperature `head` at time `t`."""
    head = np.asarray(head, dtype=float)
    return cfg.W_max * np.exp(-((head - h_opt) / cfg.w) ** 2) - cfg.lam * np.asarray(t, dtype=float)
