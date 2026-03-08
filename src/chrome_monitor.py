"""App & website monitor for Sticky Alarm."""
import ctypes
from ctypes import wintypes
import psutil
import subprocess

_BROWSER_NAMES = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"}
_user32 = ctypes.windll.user32
_WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


def _get_browser_pids():
    pids = set()
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            name = proc.info["name"]
            if name and name.lower() in _BROWSER_NAMES:
                pids.add(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids


def _get_window_titles(filter_pids=None):
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


def _get_window_handles_with_titles(filter_pids=None):
    """Return list of (hwnd, title) for matching windows."""
    results = []
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
                results.append((hwnd, buf.value))
        return True
    _user32.EnumWindows(_WNDENUMPROC(_callback), 0)
    return results


def get_active_matches(triggers):
    """Return list of trigger names that are currently active."""
    matched = []
    browser_pids = _get_browser_pids()
    browser_titles = _get_window_titles(browser_pids)
    all_titles = _get_window_titles()

    for trigger in triggers:
        name = trigger.name.lower()
        if trigger.type == "site":
            for title in browser_titles:
                if name in title.lower():
                    matched.append(trigger.name)
                    break
        elif trigger.type == "app":
            # Check running processes
            for proc in psutil.process_iter(["name"]):
                try:
                    pname = proc.info["name"]
                    if pname and name in pname.lower():
                        matched.append(trigger.name)
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
    return matched


def close_trigger_apps(triggers):
    """Kill processes matching app triggers, close browser tabs matching site triggers."""
    WM_CLOSE = 0x0010
    for trigger in triggers:
        name = trigger.name.lower()
        if trigger.type == "app":
            # Try taskkill
            proc_name = name if name.endswith(".exe") else f"{name}.exe"
            try:
                subprocess.run(
                    ["taskkill", "/IM", proc_name, "/F"],
                    capture_output=True, creationflags=0x08000000  # CREATE_NO_WINDOW
                )
            except Exception:
                pass
        elif trigger.type == "site":
            # Close browser windows whose title contains the site name
            browser_pids = _get_browser_pids()
            for hwnd, title in _get_window_handles_with_titles(browser_pids):
                if name in title.lower():
                    _user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)


def is_app_window_open(app_name):
    if not app_name:
        return False
    keyword = app_name.lower().strip()
    for title in _get_window_titles():
        if keyword in title.lower():
            return True
    return False
