"""Dataset adapters. Each adapter lives in adapters/<name>/adapter.py and defines ADAPTER (an Adapter instance)."""
import importlib


def get_adapter(name):
    """Load adapters/<name>/adapter.py and return its ADAPTER."""
    return importlib.import_module(f"adapters.{name}.adapter").ADAPTER
