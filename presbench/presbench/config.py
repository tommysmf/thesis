"""Settings of one generator run: the core knobs (here) plus the adapter's own knobs (Adapter.Params)."""
from dataclasses import dataclass, asdict, fields


@dataclass
class CoreConfig:
    delta: float = 0.95              # share of cases decided by the historical policy; the rest gets a uniformly
                                     # random decision point (SimBank-style). 0 = randomized log, 1 = pure policy
    noise_sd: float = 0.4            # case-level noise on the outcome (the same draw for every decision point)
    resamples_per_case: int = 20     # generated cases per real case (they share its signal and attributes)
    test_share: float = 0.3          # share of REAL cases in the test split (never mixed with train)
    seed: int = 0


class Settings:
    """Core and adapter knobs together. Attribute access looks in both (core first)."""

    def __init__(self, core, params):
        self.core, self.params = core, params

    def __getattr__(self, name):
        for part in (self.__dict__["core"], self.__dict__["params"]):
            if name in {f.name for f in fields(part)}:
                return getattr(part, name)
        raise AttributeError(name)

    def to_dict(self):
        return {"core": asdict(self.core), "adapter": asdict(self.params)}


def make_settings(adapter, scenario="realistic", **overrides):
    """Build Settings from the adapter's defaults, a named scenario and keyword overrides (core or adapter)."""
    values = {**adapter.scenarios.get(scenario, {}), **overrides} if scenario else dict(overrides)
    core_names = {f.name for f in fields(CoreConfig)}
    param_names = {f.name for f in fields(adapter.Params)}
    unknown = set(values) - core_names - param_names
    if unknown:
        raise ValueError(f"unknown knob(s) {sorted(unknown)}; core: {sorted(core_names)}, "
                         f"{adapter.name}: {sorted(param_names)}")
    core = CoreConfig(**{k: v for k, v in values.items() if k in core_names})
    params = adapter.Params(**{k: v for k, v in values.items() if k in param_names})
    return Settings(core, params)
