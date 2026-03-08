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
    --add-data "src/widgets.py;." --hidden-import pystray._win32 \
    src/sticky_alarm.py
# Or: build.bat (installs deps, builds, copies to 1_Export/)

# Syntax check all source files
for f in src/*.py; do python -m py_compile "$f" && echo "OK: $f"; done
```

**OneDrive note:** Edit/Write tools often fail with `EEXIST: file already exists, mkdir` on this repo's OneDrive path. Workaround: use Agent tool or Bash with `python -c "import pathlib; pathlib.Path('path').write_text(content, encoding='utf-8')"`.

## Architecture

**Python/tkinter desktop app for Windows only.** German UI throughout. `Flutter_Archive/` contains an older Flutter version (archived, not active).

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

- `popup.py` — Alarm popup: fullscreen borderless overlay or centered floating card. Sound loops via `winsound.SND_LOOP`. Grabs focus every 2s to prevent dismissal.
- `settings_window.py` — Settings with profile cards (_ProfileCard), collapsible sections, sound picker dropdown with preview playback, trigger lists. Save button (not auto-save).
- `widgets.py` — Custom tkinter widgets: RoundedButton (smooth hover transitions), RoundedEntry/Textarea (focus glow), TimeInput, NumberInput, CustomCheckbox, AutoHideScrollbar.
- `theme.py` — Dark theme tokens. Segoe UI font. All colors defined as constants.

## Conventions

- **Language**: All UI text is German
- **Single instance**: Socket lock on port 59173
- **Tray icon**: pystray with menu: Einstellungen, Alarm testen, Beenden
- **Profile defaults**: First profile is always the fallback (`config.default_profile`). Triggers without `profile_id` use the default.
- **Popup labels**: Profile-level overrides take precedence over Config-level defaults (checked in `_apply_profile_to_popup`)
