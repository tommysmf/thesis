"""All knobs of the cotton candy semi-synthetic generator in one place.

Defaults follow the specification doc ("Cotton candy toy setup: specification").
Change values by creating Config(...) with keyword arguments, or Config.from_dict(...).
"""
from dataclasses import dataclass, asdict


@dataclass
class Config:
    # ---- case evolution -----------------------------------------------------------------------
    # decision points = the real head readings (every 1.3-6.5 s depending on the batch), from "stick placed"
    # to the hottest point within 120 s, never after the real spinning ended; the case replays its real curve

    # ---- historical policy (SimBank-style) ------------------------------------------------------
    # with probability delta the case follows what the real operators did: a fixed waiting time (batches 0-14)
    # or a temperature controller (batches 15-23), with the setting drawn from comparable real runs (same
    # batch, same cold/warm machine, nearest in wear; all observable); otherwise the start moment is uniformly
    # random (as in a randomized experiment)
    delta: float = 0.95                # 1 = only the real policy (no overlap guarantee), 0 = fully randomized

    # ---- outcome: KPI = W_max*exp(-((head - h_opt)/w)^2) + noise - lam*(seconds since stick placed) -----
    W_max: float = 9.3                 # g: best possible weight
    h0: float = 65.0                   # degC: optimal head temperature for an average case (specified)
    w: float = 40.0                    # degC: width of the temperature window (wide: the real weights are almost flat)
    w_cold: float = 0.0                # degC: width below the optimum (0 = use w); smaller = starting cold hurts more
    w_hot: float = 0.0                 # degC: width above the optimum (0 = use w)
    a_wear: float = 8.0                # degC per 30 candies since maintenance above 30 (worn machines need a hotter head)
    b_humidity: float = 0.0            # degC per standard deviation of ambient humidity (off by default)
    lam: float = 0.01                  # g per s waited: the time cost in the KPI (not a loss of candy)
    noise_sd: float = 0.4              # g: case-level noise on the weight (the same draw for every start moment)

    # ---- hidden confounding (off by default): an unobserved case factor u ~ N(0, 1), e.g. how moist the
    # sugar is, shifts the optimal temperature AND the controller's threshold; it never appears in the log
    hidden_effect: float = 0.0         # degC shift of the optimum per unit of u
    hidden_policy: float = 0.0         # degC shift of the controller threshold per unit of u
    pool_size: int = 3                 # comparable real runs a setting is drawn from (nearest in wear)

    # ---- dataset ---------------------------------------------------------------------------------
    resamples_per_curve: int = 20      # generated cases per real curve (they share the curve, wear and humidity)
    test_share: float = 0.3            # share of real CURVES reserved for the test split (never mixed)
    seed: int = 0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# Named settings for different benchmark difficulties (generate.py --scenario NAME). "realistic" are the
# defaults; the others switch on one challenge each.
SCENARIOS = {
    "realistic": {},
    "hidden-confounding": dict(hidden_effect=5.0, hidden_policy=5.0),
    "asymmetric": dict(w_cold=14.0, w_hot=34.0),                  # outcome shape a quadratic cannot fit
}
