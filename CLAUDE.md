# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
# Install dependencies
pip install -r requirements.txt pyinstaller

# Run directly
python src/sticky_alarm.py

# Build standalone exe (uses python -m since pyinstaller may not be on PATH in bash)
python -m PyInstaller --onefile --windowed --name="StickyAlarm" --icon=assets/icon.ico \
    --add-data "src/config.py;." --add-data "src/scheduler.py;." \
    --add-data "src/popup.py;." --add-data "src/chrome_monitor.py;." \
    --add-data "src/foreground_tracker.py;." --add-data "src/settings_window.py;." \
    --add-data "src/autostart.py;." --add-data "src/theme.py;." \
    --add-data "src/widgets.py;." --add-data "src/break_scheduler.py;." \
    --add-data "src/break_popup.py;." \
    --add-data "assets/icon.png;assets" --add-data "assets/sounds;assets/sounds" \
    --hidden-import pystray._win32 \
    src/sticky_alarm.py
# Or: build.bat (installs deps, builds, copies to 1_Export/)

# Syntax check all source files
for f in src/*.py; do python -m py_compile "$f" && echo "OK: $f"; done
```

**OneDrive note:** Edit/Write tools often fail with `EEXIST: file already exists, mkdir` on this repo's OneDrive path. Workaround: use Agent tool or Bash with `python -c "import pathlib; pathlib.Path('path').write_text(content, encoding='utf-8')"`.

## Architecture

**Python/tkinter desktop app for Windows only.** German UI throughout.

### Core Loop & State Machine

`sticky_alarm.py` is the orchestrator. It runs a 5-second tick via `root.after()` driving the scheduler:

```
WAITING → (any profile window active) → ACTIVE → (snooze) → SNOOZED → (timeout) → ACTIVE
                                                → (confirm) → CONFIRMED → (trigger detected) → ACTIVE
                                       (window ends) → WAITING
```

The key flow after user confirms: in CONFIRMED state, the tick loop polls `chrome_monitor.get_active_matches()` every 5s. If a trigger site/app is detected, it transitions back to ACTIVE (alarm reappears). Time-based triggers accumulate via `ForegroundTracker` before firing.

### Data Model

All config is dataclasses in `config.py`, persisted as JSON to `%APPDATA%/StickyAlarm/config.json`:

- **`Config`** — top-level: list of `ScheduleProfile`s, list of `TriggerEntry`s, global defaults (popup_title, popup_text, snooze/confirm labels, sound, fullscreen)
- **`ScheduleProfile`** — named time window (TriggerSchedule with cross-midnight support) + optional per-profile alarm text overrides + launch_apps
- **`TriggerEntry`** — `name` + `type` (site|app) + optional `profile_id` + optional `time_limit_minutes`
- **Config migration**: `Config.load()` auto-detects and migrates the old flat format (start_hour/trigger_sites/trigger_apps) to the new profile-based format

### Monitoring (`chrome_monitor.py`)

Uses ctypes `EnumWindows`/`GetWindowTextW` to read browser window titles (Chrome, Edge, Firefox, Brave, Opera) for site triggers. Uses `psutil` process iteration for app triggers. Can close triggers via `PostMessageW(WM_CLOSE)` for browser tabs and `taskkill` for apps.

### UI Layer

- `popup.py` — Alarm popup: Canvas-based rounded card with shadow layer. Fullscreen = black overlay + centered card; non-fullscreen = transparent window (`-transparentcolor`) for true rounded corners. Sound loops via `winsound.SND_LOOP`. Grabs focus every 2s, pulsing icon animation, fade-in/out transitions.
- `settings_window.py` — Settings with profile cards (_ProfileCard with gold accent line + border), collapsible sections with gold dot indicators, EmojiPicker for break icon, sound picker dropdown with preview playback, trigger lists. Save button (not auto-save).
- `widgets.py` — Custom tkinter widgets: RoundedButton (cubic ease-in-out hover), RoundedEntry/Textarea (focus glow), TimeInput, NumberInput, CustomCheckbox (eased animation), CollapsibleSection, AutoHideScrollbar (smooth fade), EmojiPicker (BMP-safe preset grid), `draw_circular_progress()` (polyline-based AA ring), `round_rect()`, `fade_in_window()`/`fade_out_window()`. All use canvas-based rendering and `_lerp_color()` + `ease_in_out()` for smooth animations.
- `theme.py` — Premium dark theme tokens: Black (#0f0f0f) + White (#f5f5f5) + Gold accent (#c4a265). Segoe UI font. All colors, spacing, radii, and animation durations defined as constants.
- `break_popup.py` — Break countdown popup: Canvas-based rounded card (same pattern as popup.py) with circular progress ring (gold polyline AA), MM:SS timer centered in ring, snooze button. No sound, no grab. Auto-dismisses at 0.
- `break_scheduler.py` — Break timer state machine (IDLE/RUNNING/BREAK_DUE/BREAK_ACTIVE/SNOOZED). Tracks wall-clock time, independent from alarm scheduler.
- `foreground_tracker.py` — Accumulates per-trigger foreground time across 5s ticks for time-based trigger limits.

## Conventions

- **Language**: All UI text is German
- **Single instance**: Socket lock on port 59173
- **Tray icon**: pystray with menu: Einstellungen, Alarm testen, Beenden
- **Profile defaults**: First profile is always the fallback (`config.default_profile`). Triggers without `profile_id` use the default.
- **Popup labels**: Profile-level overrides take precedence over Config-level defaults (checked in `_apply_profile_to_popup`)
- **Save behavior**: Settings use explicit "Speichern" button (not auto-save) with success flash
- **Snooze**: Profile-level `snooze_minutes` overrides global `Config.snooze_minutes` (default 15)
- **Time-based triggers**: `TriggerEntry.time_limit_minutes > 0` makes trigger accumulate via `ForegroundTracker` instead of firing immediately
- **Sounds**: Scanned from `C:\Windows\Media` + custom via file picker; played via `winsound.SND_LOOP`
- **Break timer**: Independent periodic break reminder. Config fields prefixed with `break_`. Alarm always has priority over break popup. Break timer resets on app restart (no state persistence). Supports fullscreen mode (`break_fullscreen`) with same black overlay pattern as alarm popup.
- **Autostart**: Creates `.lnk` shortcut in Windows startup folder via PowerShell (only works from built .exe)
- **Windows APIs**: ctypes for `EnumWindows`, `GetWindowTextW`, `PostMessageW(WM_CLOSE)`; `psutil` for process detection; `taskkill /F` for app closing
