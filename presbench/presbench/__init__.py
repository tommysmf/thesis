"""presbench: turn an IoT-enriched event log into a semi-synthetic PresPM benchmark.

Core (this package, the same for every dataset):
  case.py        RealCase: what an adapter hands to the core
  adapter.py     Adapter: the contract a dataset adapter implements
  policies.py    historical policy building blocks (threshold, delay, pooled settings, hidden shift)
  outcomes.py    outcome building blocks (bell-shaped outcome with attribute-dependent optimum)
  config.py      core knobs + adapter knobs
  generator.py   generate the benchmark and write observed/ and truth/
  online.py      step-by-step environment
  validation.py  generic checks and baselines
  twostage.py    two linked decisions per case (contract, generator, online mode); see docs/CORE.md

Dataset-specific code lives in adapters/<name>/. See docs/CORE.md and docs/WRITING_AN_ADAPTER.md.
"""
from .case import RealCase, DecisionPoints
from .adapter import Adapter, AdapterParams
from .config import CoreConfig, Settings, make_settings
from .generator import generate, write
from .online import OnlineEnv
