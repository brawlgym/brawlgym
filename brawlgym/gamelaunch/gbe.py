"""
Fetch + install gbe_fork for offline / multi-instance launch.

Brawlhalla's SteamAir ANE hard-requires a working Steam API. 
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import urllib.request

APPID = 291550
REPO = "Detanup01/gbe_fork"
ASSET_NAME = "emu-win-release.7z"
VERSION_FILE = "brawlgym_gbe.json"      # in the game folder: {"tag":..., "sha256":...}

OFFLINE_INI = ("[main::connectivity]\n"
               "offline=1\n"
               "disable_networking=1\n"
               "disable_lan_only=1\n")


def _latest_release() -> dict:
    """
    Query the GitHub API for the latest gbe_fork release (tag + asset download URL).
    """
    url = f"https://api.github.com/repos/{REPO}/releases/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "brawlgym"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    asset = next((a for a in data.get("assets", []) if a.get("name") == ASSET_NAME), None)
    if asset is None:
        names = ", ".join(a.get("name", "?") for a in data.get("assets", []))
        raise RuntimeError(f"'{ASSET_NAME}' not found in latest {REPO} release (assets: {names})")
    return {"tag": data["tag_name"], "url": asset["browser_download_url"]}


def _is_x64_steam_api(name: str) -> bool:
    n = name.replace("\\", "/")
    return n.endswith("steam_api64.dll") and "/x64/" in ("/" + n)


def _sha(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _version_info(game_dir: str) -> dict:
    try:
        with open(os.path.join(game_dir, VERSION_FILE), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _fetch_dll(rel: dict) -> bytes:
    """
    Download the .7z into memory and return steam_api64.dll's bytes (extracted in memory).
    """
    from . import _sevenzip
    print(f"[gbe] fetching {rel['tag']} ({ASSET_NAME}) to memory ...")
    req = urllib.request.Request(rel["url"], headers={"User-Agent": "brawlgym"})
    with urllib.request.urlopen(req, timeout=120) as r:
        blob = r.read()
    print("[gbe] extracting steam_api64.dll in memory ...")
    return _sevenzip.extract_member(blob, _is_x64_steam_api)


def _write_offline_config(game_dir: str) -> None:
    with open(os.path.join(game_dir, "steam_appid.txt"), "w", encoding="utf-8") as f:
        f.write(str(APPID))
    settings = os.path.join(game_dir, "steam_settings")
    os.makedirs(settings, exist_ok=True)
    ini = os.path.join(settings, "configs.main.ini")
    if not os.path.exists(ini) or open(ini, encoding="utf-8").read() != OFFLINE_INI:
        with open(ini, "w", encoding="utf-8") as f:
            f.write(OFFLINE_INI)


def ensure_gbe(game_dir: str, check_updates: bool = True) -> None:
    """
    Install or update the gbe emulator + offline config in game directory.

    Asks GitHub for the latest release tag, then (re)installs the emulator into the game folder when
    the tag changed OR the game-folder DLL no longer matches the recorded sha.
    """
    dll = os.path.join(game_dir, "steam_api64.dll")
    orig = dll + ".orig"
    info = _version_info(game_dir)
    have_sha = _sha(dll) if os.path.exists(dll) else None
    dll_ok = have_sha is not None and have_sha == info.get("sha256")

    rel = None
    if check_updates:
        try:
            rel = _latest_release()
        except Exception as e:
            if dll_ok:
                print(f"[gbe] update check failed ({e}); keeping current emulator")
            else:
                raise

    if dll_ok and (rel is None or info.get("tag") == rel["tag"]):
        print("[gbe] game-folder emulator is up to date")
        _write_offline_config(game_dir)
        return
    if rel is None:
        raise RuntimeError("gbe needs (re)install but the latest release could not be fetched "
                           "(no network?)")

    reason = ("no emulator in game folder" if have_sha is None
              else "game-folder emulator is outdated/corrupt" if not dll_ok
              else f"newer release available ({rel['tag']})")
    print(f"[gbe] {reason} - installing")
    # back up the REAL dll once (it is small, ~300 KB) before the first emulator install
    if have_sha is not None and not os.path.exists(orig) and os.path.getsize(dll) < 1_000_000:
        shutil.copy2(dll, orig)
        print(f"[gbe] backed up real steam_api64.dll -> {os.path.basename(orig)}")
    data = _fetch_dll(rel)
    with open(dll, "wb") as f:
        f.write(data)
    sha = hashlib.sha256(data).hexdigest()
    with open(os.path.join(game_dir, VERSION_FILE), "w", encoding="utf-8") as f:
        json.dump({"tag": rel["tag"], "sha256": sha}, f, indent=2)
    print(f"[gbe] installed {rel['tag']} (sha {sha[:12]}...) into {game_dir}")
    _write_offline_config(game_dir)


def restore_real(game_dir: str) -> bool:
    """
    Put the real steam_api64.dll back from the .orig backup. Returns True if restored.

    Verifying steam files with Steam's "Verify integrity" will also restore the real DLL.
    """
    dll = os.path.join(game_dir, "steam_api64.dll")
    orig = dll + ".orig"
    if os.path.exists(orig):
        shutil.copy2(orig, dll)
        try:
            os.remove(os.path.join(game_dir, VERSION_FILE))
        except OSError:
            pass
        print("[gbe] restored real steam_api64.dll")
        return True
    return False
