"""
Closed-source binaries from brawlgym-core.

air_mutex_hook.dll - injected at launch so each Brawlhalla process gets private Adobe AIR
single-instance object names, letting multiple copies run at once.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
AIR_MUTEX_HOOK = os.path.join(HERE, "air_mutex_hook.dll")


def dll_path() -> str:
    """
    Absolute path to the injected multi-instance hook DLL (raises if missing).
    """
    if not os.path.exists(AIR_MUTEX_HOOK):
        raise FileNotFoundError(
            f"air_mutex_hook.dll not found at {AIR_MUTEX_HOOK} - the plugin binary is missing from this install")
    return AIR_MUTEX_HOOK
