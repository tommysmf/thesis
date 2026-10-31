"""The data an adapter hands to the core: one RealCase per usable real process instance.

The core never looks inside the raw dataset. Everything it needs about a real case is in a RealCase:
the decision signal at its real reading times, the decision window, observable attributes, the real
events that precede the window, and (optionally) more sensor channels.
"""
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


@dataclass
class RealCase:
    case_id: str              # unique id of the real instance (e.g. the run's instance number)
    group: str                # observable grouping (batch, machine, line, ...); shown in cases.csv, usable by policies
    t0: pd.Timestamp          # absolute time of t = 0 (e.g. machine on); all times below are seconds since t0
    times: np.ndarray         # sorted reading times of the decision signal
    signal: np.ndarray        # decision signal values at `times` (e.g. head temperature); the state at a decision point
    t_open: float             # first moment the intervention is possible (first decision point at or after it)
    t_close: float            # last decision point (inclusive): the intervention is forced here at the latest
    attributes: dict          # observable case attributes, written to cases.csv (numbers or strings)
    events: pd.DataFrame      # real events kept in the generated log: columns `activity`, `t` (all <= t_open)
    channels: dict = field(default_factory=dict)  # optional extra sensor channels: name -> (times, values);
                                                  # written next to the signal in sensor_stream.csv
    info: dict = field(default_factory=dict)      # adapter-private: what really happened, derived values, ...;
                                                  # never written to the observed data

    def decision_points(self):
        """Decision points = the real signal readings inside the window [t_open, t_close]."""
        idx = np.nonzero((self.times >= self.t_open) & (self.times <= self.t_close))[0]
        return DecisionPoints(idx=idx, t=self.times[idx], t_rel=self.times[idx] - self.t_open,
                              signal=self.signal[idx])

    def signal_at(self, t):
        return float(np.interp(t, self.times, self.signal))


@dataclass
class DecisionPoints:
    idx: np.ndarray       # positions of the decision points in RealCase.times
    t: np.ndarray         # seconds since t0
    t_rel: np.ndarray     # seconds since t_open
    signal: np.ndarray    # signal value at each decision point

    def __len__(self):
        return len(self.t)
