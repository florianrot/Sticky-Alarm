"""Autostart management for Sticky Alarm — adds/removes from Windows startup folder."""

import os
import subprocess
import sys


SHORTCUT_NAME = "StickyAlarm.lnk"
STARTUP_DIR = os.path.join(
    os.environ.get("APPDATA", ""),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
)


def _get_exe_path() -> str:
    """Get path to the current executable."""
    if getattr(sys, "frozen", False):
        return sys.executable  # PyInstaller .exe
    return os.path.abspath(sys.argv[0])


def is_autostart_enabled() -> bool:
    return os.path.exists(os.path.join(STARTUP_DIR, SHORTCUT_NAME))


def enable_autostart():
    shortcut_path = os.path.join(STARTUP_DIR, SHORTCUT_NAME)
    target = _get_exe_path()

    # Use PowerShell to create a .lnk shortcut (no extra dependencies needed)
    ps_script = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$sc = $ws.CreateShortcut("{shortcut_path}"); '
        f'$sc.TargetPath = "{target}"; '
        f'$sc.WorkingDirectory = "{os.path.dirname(target)}"; '
        f'$sc.Description = "Sticky Alarm - Abendroutine Trigger"; '
        f'$sc.Save()'
    )
    subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
    )


def disable_autostart():
    shortcut_path = os.path.join(STARTUP_DIR, SHORTCUT_NAME)
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
