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

PATCH_REPO = "brawlgym/brawlgym-patches"
TAG_PREFIX = "build-"      # release tag is TAG_PREFIX + the first 12 hex of the sha
TAG_SHA_LEN = 12
ASSET_NAME = "hook.bgpatch"
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
    """
    Deterministic download URL for a build: one release per build, tagged from the hash,
    so no API lookup is needed to find it.
    """
    tag = TAG_PREFIX + sha[:TAG_SHA_LEN]
    return f"https://github.com/{PATCH_REPO}/releases/download/{tag}/{ASSET_NAME}"


def _remote_changed(sha: str, cached: str):
    """
    Check if cache is stale. If a release breaks the hook and a fix is published, 
    the new release will have a different size or etag.
    """
    try:
        req = urllib.request.Request(patch_url(sha), method="HEAD", headers={"User-Agent": "brawlgym"})
        with urllib.request.urlopen(req, timeout=15) as r:
            size = r.headers.get("Content-Length")
            etag = r.headers.get("ETag", "")
    except Exception:
        return False, "offline"
    if size and int(size) != os.path.getsize(cached):
        return True, f"size {os.path.getsize(cached)} -> {size}"
    try:
        with open(cached + ".etag", encoding="utf-8") as f:
            if etag and f.read().strip() != etag:
                return True, "etag"
    except OSError:
        pass
    return False, "unchanged"


def fetch_patch(sha: str, refresh: bool = False) -> str:
    """
    Download <sha>.bgpatch into the local cache and return its path. Cached after the first call,
    so this hits the network once per game build.
    """
    dst = os.path.join(_cache_dir(), f"{sha}.bgpatch")
    if os.path.exists(dst) and not refresh:
        changed, why = _remote_changed(sha, dst)
        if not changed:
            return dst
        print(f"[patch] cached {sha[:12]}.bgpatch is stale ({why}) - refetching")

    req = urllib.request.Request(patch_url(sha), headers={"User-Agent": "brawlgym"})
    print(f"[patch] fetching {sha[:12]}.bgpatch ...")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            blob = r.read()
            etag = r.headers.get("ETag", "")
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
    if etag:
        with open(dst + ".etag", "w", encoding="utf-8") as f:
            f.write(etag)
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
