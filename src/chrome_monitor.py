"""App & website monitor for Sticky Alarm.

Two detection modes:
1. Website-Trigger: checks if any Chrome/Edge window title contains a
   configured trigger keyword (e.g. "youtube", "instagram").
   Brain.fm and other Chrome apps are safe — only matching titles trigger.
2. App-Trigger: checks if a configured process name is running
   (for non-browser apps like games).
"""

import ctypes
from ctypes import wintypes
import psutil


# Chromium browsers whose window titles we check for trigger sites
_CHROMIUM_NAMES = {"chrome.exe", "msedge.exe"}

# Windows API
_user32 = ctypes.windll.user32
_WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


def _get_browser_pids() -> set:
    """Return PIDs of all running Chromium browser processes."""
    pids = set()
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            name = proc.info["name"]
            if name and name.lower() in _CHROMIUM_NAMES:
                pids.add(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids


def _get_window_titles(filter_pids: set = None) -> list:
    """Get titles of all visible windows. If filter_pids given, only those PIDs."""
    titles = []

    def _callback(hwnd, _lparam):
        if not _user32.IsWindowVisible(hwnd):
            return True
        if filter_pids is not None:
            pid = wintypes.DWORD()
            _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value not in filter_pids:
                return True
        length = _user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            _user32.GetWindowTextW(hwnd, buf, length + 1)
            if buf.value:
                titles.append(buf.value)
        return True

    _user32.EnumWindows(_WNDENUMPROC(_callback), 0)
    return titles


def is_trigger_site_open(trigger_sites: list) -> bool:
    """Check if any browser window title contains a trigger site keyword."""
    if not trigger_sites:
        return False

    keywords = [s.lower().strip() for s in trigger_sites if s.strip()]
    if not keywords:
        return False

    for title in _get_window_titles(_get_browser_pids()):
        title_lower = title.lower()
        for kw in keywords:
            if kw in title_lower:
                return True
    return False


def is_trigger_app_running(trigger_apps: list) -> bool:
    """Check if any non-browser trigger app process is running.

    Chromium browsers (chrome.exe, msedge.exe) are automatically excluded
    — use is_trigger_site_open() for browser-based detection.
    """
    if not trigger_apps:
        return False

    targets = set()
    for name in trigger_apps:
        name_l = name.lower().strip()
        if name_l and name_l not in _CHROMIUM_NAMES:
            targets.add(name_l)

    if not targets:
        return False

    for proc in psutil.process_iter(["name"]):
        try:
            name = proc.info["name"]
            if name and name.lower() in targets:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return False


def is_app_window_open(app_name: str) -> bool:
    """Check if any visible window title contains app_name (case-insensitive)."""
    if not app_name:
        return False
    keyword = app_name.lower().strip()
    for title in _get_window_titles():
        if keyword in title.lower():
            return True
    return False


# Backwards compat
def is_chrome_running() -> bool:
    return is_trigger_app_running(["chrome.exe"])
