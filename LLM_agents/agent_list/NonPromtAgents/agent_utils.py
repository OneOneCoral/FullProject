# agents/core/agent_utils.py
import importlib.util

def module_exists(module_path: str) -> bool:
    """
    Returns True if the module can be resolved by Python.
    """
    return importlib.util.find_spec(module_path) is not None