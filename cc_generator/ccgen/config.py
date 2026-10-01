"""All knobs of the cotton candy semi-synthetic generator in one place.

Defaults follow the specification doc ("Cotton candy toy setup: specification").
Change values by creating Config(...) with keyword arguments, or Config.from_dict(...).
"""
from dataclasses import dataclass, asdict, field


@dataclass
class Config:
    # ---- decision points ---------------------------------------------------------------
    grid_seconds: float = 2.0          # decision every 2 s (the sensors are read about every 2 s)
    after_start_slowdown: float = 0.8  # real curve heats ~25% faster once spinning; slow it down when it means "still waiting"
    curve_stretch: float = 0.0         # optional extra variety: each resample stretches heating by up to +-this fraction (0 = off)

    # ---- historical policy: p_k = sigmoid(beta*(h - h_star) + gamma*(t - t_star)), clipped to [eps, 1-eps]
    beta: float = 0.3                  # per degC: confounding strength (0 = ignores the sensor)
    h_star: float = 58.0               # degC: head temperature at which a start becomes likely
    gamma: float = 0.05                # per s: impatience
    t_star: float = 22.0               # s since machine on: time at which a start becomes likely
    eps: float = 0.01                  # minimum chance of starting / waiting at every point (overlap)
    delta: float = 0.95                # share of cases that follow the historical rule; the rest get a uniformly
                                       # random start moment (like SimBank's delta: 1 = fully confounded, 0 = RCT)

    # ---- outcome: Y_k = W_max*exp(-((h_k - h_opt)/w)^2) - lam*t_k + noise
    W_max: float = 10.5                # g: best possible weight
    h0: float = 64.0                   # degC: optimal head temperature for an average case
    w: float = 22.0                    # degC: width of the temperature window
    a_wear: float = 8.0                # degC per 30 candies since maintenance above 30 (worn machines need a hotter head)
    b_humidity: float = -4.0           # degC per standard deviation of ambient humidity
    lam: float = 0.01                  # g per s of waiting
    noise_sd: float = 0.4              # g: case-level noise (the same draw for every start moment of a case)

    # ---- dataset ----------------------------------------------------------------------------
    resamples_per_curve: int = 20      # generated cases per real curve
    test_share: float = 0.3            # share of real CURVES reserved for the test split (never mixed)
    seed: int = 0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
