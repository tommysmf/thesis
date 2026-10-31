"""The adapter contract: everything the core needs to know about one dataset.

Subclass Adapter, fill in the class attributes and implement load(), policy() and outcome().
See docs/WRITING_AN_ADAPTER.md for a step-by-step guide and adapters/_template for a skeleton.
"""
from dataclasses import dataclass


@dataclass
class AdapterParams:
    """Base class for an adapter's own knobs (historical policy and outcome). Subclass it as a dataclass."""
    pass


class Adapter:
    # ---- names used in the generated data -------------------------------------------------------
    name = "unnamed"                    # short identifier, e.g. "cotton_candy"
    signal_name = "signal"              # column name of the decision signal in the observed data, e.g. "ir_head"
    signal_unit = ""                    # unit, for reports only
    signal_direction = 1                # +1: the signal rises during the window (e.g. heating), -1: it falls
                                        # (e.g. drying); used by threshold baselines and the demo. Pass it to
                                        # PooledPolicy(direction=...) too
    intervention_activity = "Intervene" # activity inserted in the log at the chosen decision point
    outcome_activity = "Outcome"        # activity inserted in the log when the outcome is measured
    outcome_name = "outcome"            # column holding the measured outcome in the log and cases.csv
    outcome_delay = 0.0                 # s between the intervention and the outcome event (cosmetic)

    Params = AdapterParams              # dataclass of the adapter's knobs, with defaults
    scenarios = {"realistic": {}}       # named settings: name -> {knob: value} (core or adapter knobs)
    sweeps = []                         # knobs to sweep in validate.py: [(knob, [values]), ...]
    model_attributes = []               # numeric attributes a simple regression method may use (demo.py)
    naive_contrast = None               # ((early_lo, early_hi), (late_lo, late_hi)) s after t_open for the naive
                                        # confounding check; None = 0-5% vs 10-40% of the median window

    # ---- required ---------------------------------------------------------------------------------
    def load(self, path, verbose=True):
        """Read the dataset at `path` and return a list of RealCase (see presbench/case.py).
        Drop instances that cannot be used, and say why when verbose."""
        raise NotImplementedError

    def policy(self, cases, params):
        """Return the historical policy (a presbench.policies.HistoricalPolicy) for these cases."""
        raise NotImplementedError

    def outcome(self, params):
        """Return the outcome model (a presbench.outcomes.Outcome)."""
        raise NotImplementedError

    # ---- optional ---------------------------------------------------------------------------------
    def realism(self, cases, generated, tables):
        """Rows comparing generated data with the real data, for validation_report.md:
        a list of (quantity, generated value, real value) tuples. Default: none."""
        return []

    def realism_notes(self, cases, generated, tables):
        """Free-form markdown lines added after the realism table (e.g. extra tables). Default: none."""
        return []
