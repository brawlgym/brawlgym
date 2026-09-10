"""
Launch one or many Brawlhalla instances for training.

Made multi-instance-safe by injecting air_mutex_hook.dll at launch and giving each instance 
its OWN bridge port.
"""
from __future__ import annotations

import os
import socket
from typing import List, Optional

from ..plugin import dll_path
from . import gbe

PROGRAM = "Brawlhalla.exe"
SWF_NAME = "BrawlhallaAir.swf"
RENDEZVOUS_PORT = 8790          # every hook connects here first; we tell it its real port
DEFAULT_BASE_PORT = 8791        # per-instance ports start here


def find_brawlhalla_dir() -> Optional[str]:
    """
    Locate the Brawlhalla install (Steam registry + library folders, then common paths).
    Ubisoft/Epic not supported (and probably won't be).
    """
    candidates = []
    try:
        from winreg import OpenKey, HKEY_CURRENT_USER, QueryValueEx
        with OpenKey(HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            steam = QueryValueEx(k, "SteamPath")[0].replace("/", os.sep)
        candidates.append(os.path.join(steam, "steamapps", "common", "Brawlhalla"))
        # other Steam library folders
        vdf = os.path.join(steam, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf):
            import re
            txt = open(vdf, encoding="utf-8", errors="ignore").read()
            for path in re.findall(r'"path"\s*"([^"]+)"', txt):
                candidates.append(os.path.join(path.replace("\\\\", "\\"),
                                                "steamapps", "common", "Brawlhalla"))
    except Exception:
        pass
    candidates.append(r"C:\Program Files (x86)\Steam\steamapps\common\Brawlhalla")
    for d in candidates:
        if os.path.exists(os.path.join(d, PROGRAM)):
            return d
    return None


def _rendezvous_assign(target_port: int, timeout: float, players: Optional[int] = None) -> None:
    """
    Accept the just-booted hook on the rendezvous port, tell it its real port and wait for it to drop off cleanly
    """
    rv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    rv.bind(("127.0.0.1", RENDEZVOUS_PORT))
    rv.listen(1)
    rv.settimeout(timeout)
    try:
        conn, _ = rv.accept()                       # hook connected to rendezvous
        with conn:
            msg = f"setport {target_port}\n"
            if players:
                msg += f"setcount {players}\n"
            conn.sendall(msg.encode())
            conn.settimeout(timeout)
            # the hook reconnects to target_port and closes this socket -> recv returns b''
            while True:
                try:
                    if not conn.recv(4096):
                        break
                except socket.timeout:
                    break
    finally:
        rv.close()


def launch_instances(n: int = 1,
                     base_port: int = DEFAULT_BASE_PORT,
                     players: Optional[int] = None,
                     game_dir: Optional[str] = None,
                     ensure_gbe: bool = True,
                     check_gbe_updates: bool = True,
                     auto_minimize: bool = False,
                     auto_mute: bool = False,
                     args: Optional[List[str]] = None,
                     map_name: Optional[str] = None,
                     handoff_timeout: float = 90.0) -> List[int]:
    """
    Boot n Brawlhalla instances. Returns the ports [base_port .. base_port+n-1].
    """
    from ..envs.match import brawlgym_core
    if brawlgym_core is None:
        raise ImportError("brawlgym_core (compiled engine) is not importable")

    game_dir = game_dir or find_brawlhalla_dir()
    if not game_dir:
        raise FileNotFoundError("Brawlhalla install not found; pass game_dir=")
    exe = os.path.join(game_dir, PROGRAM)
    dll = dll_path()
    launch_args = args if args is not None else ["-noeac"]

    if ensure_gbe:
        gbe.ensure_gbe(game_dir, check_updates=check_gbe_updates)

    # the level set is read at startup, so this has to happen before any instance boots
    from ..utils.common_values import DEFAULT_MAP, MAP_ENV_VAR
    locked = map_name or DEFAULT_MAP
    brawlgym_core.set_map(locked)
    os.environ[MAP_ENV_VAR] = locked
    print(f"[launch] map set to {locked}")

    from . import window
    have_pycaw = window.pycaw_available()
    if auto_mute and not have_pycaw:
        print("[launch] pycaw not installed - cannot mute (pip install pycaw)")

    ports: List[int] = []
    pids: List[int] = []
    pending: List[int] = []
    for i in range(n):
        target = base_port + i
        pid = brawlgym_core.launch_instance(exe, launch_args, dll, game_dir)
        print(f"[launch] instance {i}: pid={pid} -> port {target}"
              + (f" (roster {players})" if players else ""))
        try:
            _rendezvous_assign(target, handoff_timeout, players)
        except socket.timeout:
            raise TimeoutError(
                f"instance {i} (pid {pid}) never reached the rendezvous port {RENDEZVOUS_PORT} - it "
                "may not have booted; check that the hook is injected and the game launched")
        ports.append(target)
        pids.append(pid)
        pending += _apply_window_prefs([pid], auto_minimize, auto_mute, have_pycaw)
    print(f"[launch] {n} instance(s) up on ports {ports}")

    if pending:
        pending = _apply_window_prefs(pending, auto_minimize, auto_mute, have_pycaw)
    if pending:
        print(f"[launch] no window/audio session yet for pid(s) {pending} - left as they are")
    return ports


def _apply_window_prefs(pids, minimize, mute, have_pycaw) -> List[int]:
    """
    Minimize and ALWAYS set the mute state to mute for each game.
    """
    from . import window
    pending = []
    for pid in pids:
        done = True
        if minimize and not window.minimize_pids([pid]):
            done = False
        # with pycaw present the desired state is always enforced, mute or unmute
        if have_pycaw and not window.mute_pids([pid], mute=mute):
            done = False
        if not done:
            pending.append(pid)
    return pending
