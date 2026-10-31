"""Outcome models: what the KPI would have been for every possible decision point.

An outcome answers, for a case and its decision points (see Outcome):
  expected(case, dp, hidden)  -> (measure, kpi): the expected measured outcome (logged, e.g. a weight) and the
                                 expected KPI (what a method optimises) at every decision point
  truth_info(case, hidden)    -> extra per-case values for case_truth.csv (e.g. the case's optimum)
  uses_hidden                 -> True if the outcome depends on the hidden factor u

The core adds the case-level noise (the same draw for every decision point of a case) to the measure and
the KPI, and computes the "observable" expectation (averaged over u) when uses_hidden is True.

Building block:
  BellOutcome   measure = height * exp(-((signal - optimum) / width)^2), with an optimum that shifts with
                case attributes (and optionally u); KPI = measure - time_cost * seconds since t_open
Adapters with other outcomes subclass Outcome.
"""
import numpy as np


class Outcome:
    uses_hidden = False

    def expected(self, case, dp, hidden):
        raise NotImplementedError

    def truth_info(self, case, hidden):
        return {}


class BellOutcome(Outcome):
    """Bell-shaped outcome in the signal value at the decision point.

    height, optimum, width: peak value, signal value of the peak (average case), width of the window
    width_low, width_high:  optional different widths below / above the optimum (0 = use width)
    shifts:      list of (attribute name, change of the optimum per `scale`, center, scale); the attribute is
                 looked up in case.info first, then case.attributes. The optimum is
                 optimum + sum(change * (value - center) / scale) + hidden_effect * u
    hidden_effect: shift of the optimum per unit of the hidden factor u (0 = off)
    time_cost:   KPI cost per second waited after t_open
    """

    def __init__(self, height, optimum, width, width_low=0.0, width_high=0.0, shifts=(), hidden_effect=0.0,
                 time_cost=0.0):
        self.height, self.optimum, self.width = height, optimum, width
        self.width_low, self.width_high = width_low, width_high
        self.shifts, self.hidden_effect, self.time_cost = list(shifts), hidden_effect, time_cost
        self.uses_hidden = bool(hidden_effect)

    def case_optimum(self, case, hidden):
        h = self.optimum
        for name, change, center, scale in self.shifts:
            value = case.info[name] if name in case.info else case.attributes[name]
            h = h + change * (value - center) / scale
        return h + self.hidden_effect * hidden

    def expected(self, case, dp, hidden):
        h_opt = self.case_optimum(case, hidden)
        s = np.asarray(dp.signal, dtype=float)
        width = np.where(s < h_opt, self.width_low or self.width, self.width_high or self.width)
        measure = self.height * np.exp(-((s - h_opt) / width) ** 2)
        return measure, measure - self.time_cost * np.asarray(dp.t_rel, dtype=float)

    def truth_info(self, case, hidden):
        return {"optimum": self.case_optimum(case, hidden)}
