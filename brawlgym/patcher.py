"""
Fetch and apply the SWF hook patch matching the installed Brawlhalla build.

A patch is version-locked to one exact BrawlhallaAir.swf. CI publishes one per game build,
named by the pristine SWF's sha256, so the lookup is a direct GET with no API call.
"""
from __future__ import annotations

import filecmp
import hashlib
import os
import shutil
import urllib.error
import urllib.request
import zlib
from typing import Optional

PATCH_REPO = "brawlgym/brawlgym-patches"
TAG_PREFIX = "build-"      # release tag is TAG_PREFIX + the first 12 hex of the sha
TAG_SHA_LEN = 12
ASSET_NAME = "hook.bgpatch"
SWF_NAME = "BrawlhallaAir.swf"
BACKUP_SUFFIX = ".brawlgym-orig"      # matches brawlgym_core's own backup name
HOOK_MARKERS = (b"belTickOnce", b"belSetSimC")   # hook methods, present only in a patched SWF


def _cache_dir() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "brawlgym", "patches")
    os.makedirs(d, exist_ok=True)
    return d


def _swf_body(blob: bytes) -> bytes:
    """
    The decompressed SWF body. Brawlhalla ships CWS (zlib); FWS is stored.
    """
    sig, rest = blob[:3], blob[8:]
    if sig == b"CWS":
        return zlib.decompress(rest)
    if sig == b"FWS":
        return rest
    raise ValueError(f"unsupported SWF signature {sig!r}")


def swf_is_patched(path: str) -> bool:
    """
    True if this SWF already carries the brawlgym hook. The hook's method names live in the ABC
    string pool, so scanning the decompressed body tells one of ours from a vanilla game file.
    """
    with open(path, "rb") as f:
        body = _swf_body(f.read())
    return any(m in body for m in HOOK_MARKERS)


def _resolve_game_dir(game_dir: Optional[str]) -> str:
    if game_dir is None:
        from .gamelaunch import find_brawlhalla_dir
        game_dir = find_brawlhalla_dir()
        if not game_dir:
            raise FileNotFoundError("Brawlhalla install not found; pass game_dir=")
    return game_dir


def _swz_key_ok(game_dir: Optional[str] = None) -> bool:
    """
    True if the live SWF and the installed .swz archives are from the same build.

    The archive key is a constant in the SWF's own bytecode, so the game data only decrypts with
    the SWF it shipped with. Patching the SWF leaves that constant alone, which makes this a cheap
    build-agreement test that works on a hooked SWF just as well as on a vanilla one.
    """
    from .envs.match import brawlgym_core
    try:
        brawlgym_core.list_maps()
        return True
    except RuntimeError as e:
        if "key not found" in str(e).lower():
            return False
        raise


def repair_pristine(game_dir: Optional[str] = None, timeout: float = 600.0) -> None:
    """
    Get the current build's original SWF back on disk by having Steam re-download it.

    Reached when the installed game data is newer than the SWF we hold: the game updated and the
    original bytes for the new build are not on this machine any more, so there is nothing local
    to rebuild them from. Set BRAWLGYM_NO_AUTO_VERIFY=1 to be told what to do instead.
    """
    import time
    from .gamelaunch.gbe import APPID

    game_dir = _resolve_game_dir(game_dir)
    live = os.path.join(game_dir, SWF_NAME)
    manual = (f"Brawlhalla has updated and the original {SWF_NAME} for the new build is no longer "
              f"on disk. Verify the game files in Steam (Properties -> Installed Files -> Verify "
              f"integrity) and run again.")

    if os.environ.get("BRAWLGYM_NO_AUTO_VERIFY"):
        raise RuntimeError(manual)

    print(f"[patch] the game updated and the original {SWF_NAME} for the new build is gone; "
          "asking Steam to restore it")
    try:
        os.startfile(f"steam://validate/{APPID}")      # noqa: S606 - Steam's own handler
    except OSError as e:
        raise RuntimeError(manual) from e

    print("[patch] waiting for Steam to finish verifying (this takes a few minutes) ...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(3.0)
        try:
            if not swf_is_patched(live) and _swz_key_ok(game_dir):
                print(f"[patch] {SWF_NAME} restored")
                return
        except Exception:
            pass        # mid-write, or a partial file: keep waiting
    raise RuntimeError(f"Steam did not restore {SWF_NAME} within {timeout:.0f}s. " + manual)


def ensure_pristine(game_dir: Optional[str] = None) -> None:
    """
    Make sure the original SWF we are about to hash and patch belongs to the installed build.

    A vanilla live file needs nothing - pristine_swf() captures it. A hooked live file is only
    trustworthy while it still agrees with the installed game data; once it doesn't, both it and
    the backup are from a build the game has moved past, and only Steam can supply the new one.
    """
    game_dir = _resolve_game_dir(game_dir)
    live = os.path.join(game_dir, SWF_NAME)
    try:
        if not swf_is_patched(live):
            return
    except Exception:
        return                                  # unreadable: pristine_swf() warns and carries on
    if os.path.exists(live + BACKUP_SUFFIX) and _swz_key_ok(game_dir):
        return
    repair_pristine(game_dir)


def pristine_swf(game_dir: Optional[str] = None) -> str:
    """
    Path to the unpatched SWF for the build that is installed right now, re-capturing the backup
    when the game has updated.

    A game update replaces the live SWF with a new vanilla and leaves the previous backup sitting
    next to it. Trusting that backup means hashing the old build, fetching the old build's patch
    (a cache hit, so not even a failed download), and writing a stale SWF back over the updated
    game — which then disagrees with the updated .swz files. So the backup is re-captured whenever
    the live file is a vanilla one, and trusted only when the live file is one of ours.
    """
    game_dir = _resolve_game_dir(game_dir)
    live = os.path.join(game_dir, SWF_NAME)
    if not os.path.exists(live):
        raise FileNotFoundError(f"{SWF_NAME} not found in {game_dir}")
    backup = live + BACKUP_SUFFIX

    try:
        patched = swf_is_patched(live)
    except Exception as e:
        # Can't tell what the live file is. Keep the old behaviour rather than refusing to run,
        # but say so: if the game just updated, this is the case that injects a stale build.
        print(f"[patch] WARNING: cannot read {SWF_NAME} ({e}); falling back to the existing backup")
        return backup if os.path.exists(backup) else live

    if not patched:
        # Fresh install, or Steam has just updated the game: the live file IS this build's pristine.
        if not os.path.exists(backup) or not filecmp.cmp(backup, live, shallow=False):
            shutil.copyfile(live, backup)
            print(f"[patch] captured pristine {SWF_NAME} for the installed build")
        return live

    if not os.path.exists(backup):
        raise RuntimeError(
            f"{SWF_NAME} is already patched but its {BACKUP_SUFFIX} backup is missing, so the "
            "pristine bytes for this build are gone. Verify the game files in Steam (Properties "
            "-> Installed Files -> Verify integrity) to restore the original SWF, then run again.")
    return backup


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
    ensure_pristine(game_dir)          # a game update leaves no local copy of the new original
    sha = swf_sha256(pristine_swf(game_dir))
    path = fetch_patch(sha, refresh=refresh)
    brawlgym_core.inject_swf(path)
    print(f"[patch] injected build {sha[:12]}")
    return path
