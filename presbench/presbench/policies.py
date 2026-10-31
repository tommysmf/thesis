"""Historical policies: who decided when to intervene in the training log.

A policy answers two questions for a case (see HistoricalPolicy):
  sample()        draw the historical decision point (and the setting that led to it)
  distribution()  the EXACT chance of every decision point, given only what a method can observe

The core mixes the policy with a share 1 - delta of uniformly random decision points (SimBank-style), so the
final propensity is  delta * distribution() + (1 - delta) / n.

Building blocks:
  threshold_point     intervene at the first reading at or above a threshold (a controller); with direction=-1
                      at the first reading at or below it (for falling signals, e.g. moisture)
  delay_point         intervene at the first decision point at least `delay` s after t_open (a timer)
  PooledPolicy        per case, a rule type (threshold or delay) and a pool of settings drawn uniformly;
                      covers "the operator used one of these real settings" and adds an optional hidden shift
Adapters with other policies subclass HistoricalPolicy.
"""
from math import erf, sqrt
import numpy as np


def threshold_point(signal, threshold, direction=1):
    """First decision point whose signal has reached `threshold` (else the last point).
    direction=+1: signal >= threshold (rising signal); direction=-1: signal <= threshold (falling signal)."""
    hit = np.nonzero(direction * np.asarray(signal) >= direction * threshold)[0]
    return int(hit[0]) if len(hit) else len(signal) - 1


def delay_point(t_rel, delay):
    """First decision point at least `delay` s after t_open (else the last point)."""
    return int(min(np.searchsorted(t_rel, delay, side="left"), len(t_rel) - 1))


def point_distribution(points, n):
    """Share of `points` (decision point indices) landing on each of n points."""
    return np.bincount(np.asarray(points, dtype=int), minlength=n)[:n] / len(points)


def threshold_distribution_hidden(signal, threshold, sd, direction=1):
    """Exact chance of each point for a threshold rule whose threshold is shifted by sd * u, u ~ N(0, 1)
    unobserved: it fires at the first k where the running maximum (direction=-1: minimum) of the signal reaches
    the threshold. A falling signal is handled as the rising signal -signal with threshold -threshold."""
    if direction < 0:
        signal, threshold = -np.asarray(signal, dtype=float), -threshold
    run_max = np.maximum.accumulate(np.asarray(signal, dtype=float))
    cdf = np.array([0.5 * (1 + erf((m - threshold) / (sd * sqrt(2)))) for m in run_max])
    p = np.diff(np.concatenate([[0.0], cdf]))
    p[-1] += 1.0 - cdf[-1]                 # never reached: forced at the last point
    return p


class HistoricalPolicy:
    """Interface. `case` is a RealCase, `dp` its DecisionPoints, `hidden` the case's unobserved factor u."""

    def sample(self, case, dp, hidden, rng):
        """Return (arm name, setting or nan, decision point index). Use `rng` for all randomness."""
        raise NotImplementedError

    def distribution(self, case, dp):
        """Exact P(decision point k) for this policy, conditional only on observable information
        (integrate out the hidden factor and any unobserved setting)."""
        raise NotImplementedError


class PooledPolicy(HistoricalPolicy):
    """Per case: a rule type and a pool of real settings, one drawn uniformly at random.

    kinds:  case_id -> "threshold" or "delay"
    pools:  case_id -> list of settings (signal thresholds, or delays in s after t_open)
    arms:   optional case_id -> arm name written to case_truth.csv (default: the rule type)
    hidden_shift: threshold rules move by hidden_shift * u (hidden confounding); 0 = off
    direction:    +1 if the threshold is reached from below (rising signal), -1 from above (falling signal)
    The pools must be chosen from observable information only, so distribution() is a valid propensity.
    """

    def __init__(self, kinds, pools, arms=None, hidden_shift=0.0, direction=1):
        self.kinds, self.pools, self.arms, self.hidden_shift = kinds, pools, arms or {}, hidden_shift
        self.direction = direction

    def sample(self, case, dp, hidden, rng):
        kind, pool = self.kinds[case.case_id], self.pools[case.case_id]
        setting = float(rng.choice(pool))
        if kind == "threshold":
            k = threshold_point(dp.signal, setting + self.hidden_shift * hidden, self.direction)
        else:
            k = delay_point(dp.t_rel, setting)
        return self.arms.get(case.case_id, kind), setting, k

    def distribution(self, case, dp):
        kind, pool = self.kinds[case.case_id], self.pools[case.case_id]
        if kind == "threshold":
            if self.hidden_shift:
                return np.mean([threshold_distribution_hidden(dp.signal, thr, self.hidden_shift, self.direction)
                                for thr in pool], axis=0)
            return point_distribution([threshold_point(dp.signal, thr, self.direction) for thr in pool], len(dp))
        return point_distribution([delay_point(dp.t_rel, d) for d in pool], len(dp))
