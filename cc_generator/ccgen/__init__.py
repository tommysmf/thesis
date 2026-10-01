"""Semi-synthetic cotton candy generator: when to start spinning, on real heating curves."""
from .config import Config
from .data import load_curves
from .generator import generate, write
from .online import CottonCandyEnv
