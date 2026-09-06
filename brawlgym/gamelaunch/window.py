"""
Minimize + mute Brawlhalla windows/audio - for running instances in the background.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

_user32 = ctypes.windll.user32
_SW_MINIMIZE = 6
_EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _windows_where(predicate):
    found = []

    def cb(hwnd, _):
        try:
            if _user32.IsWindowVisible(hwnd) and predicate(hwnd):
                found.append(hwnd)
        except Exception:
            pass
        return True

    _user32.EnumWindows(_EnumProc(cb), 0)
    return found


def _pid_of(hwnd):
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def _title_of(hwnd):
    n = _user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    _user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def minimize_pids(pids) -> int:
    """
    Minimize the visible top-level windows owned by any of ``pids``. Returns how many minimized.
    """
    want = set(pids)
    hwnds = _windows_where(lambda h: _pid_of(h) in want)
    for h in hwnds:
        _user32.ShowWindow(h, _SW_MINIMIZE)
    return len(hwnds)


def minimize_title(substr: str = "Brawlhalla") -> int:
    """
    Minimize visible top-level windows whose title contains ``substr`` (rlgym-style).
    """
    hwnds = _windows_where(lambda h: substr in _title_of(h))
    for h in hwnds:
        _user32.ShowWindow(h, _SW_MINIMIZE)
    return len(hwnds)


def pycaw_available() -> bool:
    """
    True if pycaw can be imported (needed for muting/unmuting).
    """
    try:
        import pycaw.pycaw  # noqa: F401
        return True
    except ImportError:
        return False


def _sessions():
    """
    All audio sessions, or None if pycaw is missing/unavailable (quiet - caller decides to warn).
    """
    try:
        from pycaw.pycaw import AudioUtilities
    except ImportError:
        return None
    try:
        return AudioUtilities.GetAllSessions()
    except Exception as e:
        print(f"[window] could not enumerate audio sessions: {e}")
        return None


def mute_pids(pids, mute: bool = True) -> int:
    """
    Mute (or unmute) the audio sessions of the given process ids. Returns how many changed.
    """
    sessions = _sessions()
    if sessions is None:
        return 0
    want = set(pids)
    n = 0
    for s in sessions:
        if s.Process and s.Process.pid in want:
            s.SimpleAudioVolume.SetMute(1 if mute else 0, None)
            n += 1
    return n


def mute_name(name: str = "Brawlhalla.exe", mute: bool = True) -> int:
    """
    Mute (or unmute) every audio session whose process name matches name.
    """
    sessions = _sessions()
    if sessions is None:
        return 0
    n = 0
    for s in sessions:
        if s.Process and s.Process.name().lower() == name.lower():
            s.SimpleAudioVolume.SetMute(1 if mute else 0, None)
            n += 1
    return n
