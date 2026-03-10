# CLAUDE.md — Sticky Alarm Android

## Build & Run

```bash
# Build debug APK
cd Android/
./gradlew assembleDebug
# Output: app/build/outputs/apk/debug/app-debug.apk

# Install on connected device
adb install app/build/outputs/apk/debug/app-debug.apk

# Build release APK (needs signing config in app/build.gradle.kts)
./gradlew assembleRelease

# Run lint
./gradlew lint
```

## Architecture

**Kotlin + Jetpack Compose + Material Design 3 native Android app.**
German UI throughout. Dark theme only (Black + White, no Gold).

### Core Loop & State Machine

`AlarmForegroundService` is the orchestrator. It runs a 5-second tick via `Handler.postDelayed()` driving both schedulers:

**Alarm State Machine:**
```
WAITING → (profile window active) → ACTIVE → (snooze) → SNOOZED → (timeout) → ACTIVE
                                            → (confirm) → CONFIRMED → (app detected) → ACTIVE
                                   (window ends) → WAITING
```

**Break Timer State Machine:**
```
IDLE → (enabled) → RUNNING → (interval elapsed) → BREAK_DUE → BREAK_ACTIVE → (countdown done) → RUNNING
                                                              → SNOOZED → (timeout) → BREAK_DUE
```

Alarm always has priority over break popup.

### Data Model

Config stored as JSON in DataStore Preferences at app-internal storage:

- **Config** — top-level: list of ScheduleProfiles, list of TriggerEntries, global defaults
- **ScheduleProfile** — named time window + optional per-profile alarm text overrides + launch_apps (package names)
- **TriggerEntry** — package name + type="app" + optional profile_id + optional time_limit_minutes
- **Persistence**: kotlinx.serialization JSON via DataStore

### App Monitoring

Uses `UsageStatsManager` to detect foreground app package name every 5 seconds. Requires PACKAGE_USAGE_STATS permission (manual toggle in system settings). Only detects apps, NOT browser tabs/websites.

### UI Layer

- **AlarmActivity/AlarmScreen** — Full-screen intent, shows over lock screen, 3-burst vibration (no sound), snooze + confirm buttons
- **BreakActivity/BreakScreen** — Break countdown popup (fullscreen or notification-only mode), MM:SS timer, progress bar, auto-dismiss, snooze button
- **SettingsScreen** — Profile cards, app trigger lists with app picker dialog (icons + human-readable names), break timer settings, explicit save button
- **Theme** — Material Design 3 dark color scheme with PC app palette (#0f0f0f background, #f5f5f5 text, #ffffff accent)

## Project Structure

```
app/src/main/kotlin/com/stickyalarm/
├── StickyAlarmApp.kt          — Hilt Application
├── MainActivity.kt            — Single Activity, hosts SettingsScreen
├── data/
│   ├── model/                 — Config, ScheduleProfile, TriggerEntry, TriggerSchedule
│   └── ConfigRepository.kt   — DataStore JSON persistence
├── domain/
│   ├── AlarmScheduler.kt      — Alarm state machine
│   ├── BreakScheduler.kt      — Break timer state machine (with reset + remaining time)
│   ├── ForegroundTracker.kt   — Per-trigger time accumulation
│   ├── AppMonitor.kt          — UsageStatsManager wrapper
│   └── AppLauncher.kt         — Launch apps by package name
├── service/
│   ├── AlarmForegroundService.kt — 5s tick loop, orchestrator, screen-off detection
│   ├── BootReceiver.kt          — Autostart after reboot
│   └── NotificationHelper.kt    — 3 notification channels (service/alarm/break)
├── ui/
│   ├── theme/                 — Color.kt, Type.kt, Theme.kt
│   ├── alarm/                 — AlarmActivity, AlarmScreen
│   ├── breakpopup/            — BreakActivity, BreakScreen
│   └── settings/              — SettingsScreen, ProfileCard, AppPickerDialog,
│                                BreakSection, SettingsViewModel
└── util/
    ├── PackageUtils.kt        — Installed app listing with icons
    └── PermissionHelper.kt    — Permission checks + request helpers
```

## Conventions

- **Language**: All UI text is German (centralized in res/values/strings.xml)
- **Foreground Service**: Minimal persistent notification (IMPORTANCE_MIN, deferred)
- **Service Persistence**: stopWithTask=false + onTaskRemoved restart
- **App Detection**: UsageStatsManager (no Accessibility Service)
- **No website triggers**: Only app triggers (package names)
- **No sound**: Alarm uses vibration only (3 short bursts)
- **Save behavior**: Explicit "Speichern" button (not auto-save) with success flash
- **Profile system**: Same as PC — first profile is default, triggers link to profiles
- **Break popup**: Two modes — fullscreen overlay or notification-only (configurable)
- **Screen-off detection**: 5+ min screen off → break timer resets
- **Boot**: RECEIVE_BOOT_COMPLETED restarts foreground service
- **DI**: Hilt for dependency injection
- **Persistence**: DataStore Preferences with kotlinx.serialization JSON
