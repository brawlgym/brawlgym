"""
Fetch and apply the SWF hook patch matching the installed Brawlhalla build.

A patch is version-locked to one exact BrawlhallaAir.swf. CI publishes one per game build,
named by the pristine SWF's sha256, so the lookup is a direct GET with no API call.
"""
from __future__ import annotations

import hashlib
import os
import urllib.error
import urllib.request
from typing import Optional

PATCH_REPO = "chrisrca/brawlgym-patches"
PATCH_TAG = "patches"
SWF_NAME = "BrawlhallaAir.swf"
BACKUP_SUFFIX = ".brawlgym-orig"      # matches brawlgym_core's own backup name


def _cache_dir() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "brawlgym", "patches")
    os.makedirs(d, exist_ok=True)
    return d


def pristine_swf(game_dir: Optional[str] = None) -> str:
    """
    Path to the unpatched SWF: the .brawlgym-orig backup if injection already ran, else the
    live file. Mirrors brawlgym_core's pristine_swf_path() so both hash the same bytes.
    """
    if game_dir is None:
        from .gamelaunch import find_brawlhalla_dir
        game_dir = find_brawlhalla_dir()
        if not game_dir:
            raise FileNotFoundError("Brawlhalla install not found; pass game_dir=")
    live = os.path.join(game_dir, SWF_NAME)
    if not os.path.exists(live):
        raise FileNotFoundError(f"{SWF_NAME} not found in {game_dir}")
    backup = live + BACKUP_SUFFIX
    return backup if os.path.exists(backup) else live


def swf_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_url(sha: str) -> str:
    return f"https://github.com/{PATCH_REPO}/releases/download/{PATCH_TAG}/{sha}.bgpatch"


def fetch_patch(sha: str, refresh: bool = False) -> str:
    """
    Download <sha>.bgpatch into the local cache and return its path. Cached after the first call,
    so this hits the network once per game build.
    """
    dst = os.path.join(_cache_dir(), f"{sha}.bgpatch")
    if os.path.exists(dst) and not refresh:
        return dst

    req = urllib.request.Request(patch_url(sha), headers={"User-Agent": "brawlgym"})
    print(f"[patch] fetching {sha[:12]}.bgpatch ...")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            blob = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(
                f"no hook patch published for this Brawlhalla build yet (swf {sha[:12]}). "
                "One is derived and published automatically after a game update - check back "
                "shortly, or report it if the build stays unsupported.") from None
        raise

    tmp = dst + ".part"
    with open(tmp, "wb") as f:
        f.write(blob)
    os.replace(tmp, dst)
    print(f"[patch] cached -> {dst} ({len(blob)} bytes)")
    return dst


def inject(game_dir: Optional[str] = None, refresh: bool = False) -> str:
    """
    Patch the installed game with the hook built for its exact build. Returns the patch path.
    """
    from .envs.match import brawlgym_core
    if brawlgym_core is None:
        raise ImportError("brawlgym requires the brawlgym_core engine module; install it and "
                          "ensure it is importable")
    sha = swf_sha256(pristine_swf(game_dir))
    path = fetch_patch(sha, refresh=refresh)
    brawlgym_core.inject_swf(path)
    print(f"[patch] injected build {sha[:12]}")
    return path
