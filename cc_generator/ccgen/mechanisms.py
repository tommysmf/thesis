"""The specified mechanisms: the historical policy and the outcome.

Plain functions of the case state, so methods, baselines and the online mode use exactly the same
definitions as the generator. The state at decision point k is the real head reading at its real,
irregular time t_k; the policy and the outcome both use that reading.
"""
from math import erf, sqrt
import numpy as np


# ---- historical policy ------------------------------------------------------------------------
def last_point(t_rel):
    return len(t_rel) - 1


def controller_point(head_obs, threshold):
    """Temperature controller: start at the first reading at or above the threshold (else the last point)."""
    hit = np.nonzero(np.asarray(head_obs) >= threshold)[0]
    return int(hit[0]) if len(hit) else len(head_obs) - 1


def fixed_wait_point(t_rel, wait):
    """Fixed waiting time: start at the first reading at least `wait` s after "stick placed" (else the last)."""
    return int(min(np.searchsorted(t_rel, wait, side="left"), len(t_rel) - 1))


def point_distribution(points, n):
    """Share of `points` (start indices) landing on each of n decision points."""
    return np.bincount(np.asarray(points, dtype=int), minlength=n)[:n] / len(points)


def controller_distribution_hidden(head, threshold, sd):
    """Exact chance of each start point for a controller whose threshold is threshold + sd*u, u ~ N(0, 1)
    unobserved: it starts at the first k where the running maximum of the readings reaches the threshold."""
    run_max = np.maximum.accumulate(np.asarray(head, dtype=float))
    cdf = np.array([0.5 * (1 + erf((m - threshold) / (sd * sqrt(2)))) for m in run_max])
    p = np.diff(np.concatenate([[0.0], cdf]))
    p[-1] += 1.0 - cdf[-1]                 # never reached: forced start at the last point
    return p


# ---- outcome ----------------------------------------------------------------------------------
def optimal_head(wear, hum_z, cfg, hidden=0.0):
    """Case-specific optimal head temperature (degC). `hidden` is the unobserved case factor (if switched on)."""
    return cfg.h0 + cfg.a_wear * (wear - 30.0) / 30.0 + cfg.b_humidity * hum_z + cfg.hidden_effect * hidden


def expected_weight(head, h_opt, cfg):
    """Expected candy weight (g) when spinning starts at head temperature `head`.
    The window is w wide on both sides, or w_cold below and w_hot above the optimum when those are set."""
    head = np.asarray(head, dtype=float)
    width = np.where(head < h_opt, cfg.w_cold or cfg.w, cfg.w_hot or cfg.w)
    return cfg.W_max * np.exp(-((head - h_opt) / width) ** 2)


def expected_kpi(head, t_rel, h_opt, cfg):
    """Expected KPI: weight minus a cost of lam g per second waited after "stick placed"."""
    return expected_weight(head, h_opt, cfg) - cfg.lam * np.asarray(t_rel, dtype=float)
