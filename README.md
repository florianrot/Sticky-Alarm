# Sticky Alarm

**ADHS-freundlicher Abendroutine-Trigger für Windows & Android.**

Sticky Alarm erinnert dich jeden Abend daran, deine Abendroutine zu starten — und bleibt so lange hartnäckig, bis du es tust. Perfekt für alle, die abends in YouTube, Instagram & Co. versinken und das Schlafen vergessen.

## Features

### Kern-Features (beide Plattformen)
- **Zeitprofil-basiertes Scheduling** — Mehrere Zeitfenster mit individuellen Einstellungen
- **App-Trigger** — Erkennt automatisch ob ablenkende Apps aktiv sind und löst den Alarm erneut aus
- **Zeit-basierte Trigger** — Definiere Zeitlimits pro App (z.B. 15 Min Claude → Alarm)
- **Nicht-ignorierbares Alarm-Popup** — Fullscreen-Overlay oder zentrierte Karte
- **Schlummern** — Konfigurierbarer Snooze pro Profil (Standard: 15 Min)
- **Pausentimer** — Regelmäßige Pausen-Erinnerungen mit Countdown
- **Dark Theme** — Minimalistisches, dunkles Design

### Windows
- **Website-Trigger** — Erkennt Browser-Tabs (Chrome, Edge, Firefox, Brave, Opera)
- **Auto-Start Apps** — Startet konfigurierte Apps bei Bestätigung
- **Alarm-Sounds** — Windows .wav Dateien als Sound
- **System Tray** — Läuft unauffällig im Hintergrund
- **Windows Autostart** — Optional beim Hochfahren starten

### Android
- **Immersiver Fullscreen** — Alarm/Pausen-Popup ohne Status- und Navigationsleiste
- **Overlay-Trick** — Zuverlässige Popup-Anzeige auch aus dem Hintergrund
- **Lock-Screen Awareness** — Pausentimer pausiert bei gesperrtem Gerät
- **Session-basierte Zeit-Trigger** — Counter resettet nach 5 Min Inaktivität
- **Autostart nach Neustart** — Optional, muss explizit aktiviert werden
- **Vibration** — 3-Burst-Pattern statt Sound

## Installation

### Windows

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# App starten
python src/sticky_alarm.py

# Als .exe bauen
build.bat
```

### Android

```bash
cd Android/
./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

## Projektstruktur

```
Sticky_Alarm/
├── src/                          # Windows (Python/tkinter)
│   ├── sticky_alarm.py           # Entry Point + Tick Loop
│   ├── config.py                 # Config Dataclasses + JSON
│   ├── scheduler.py              # Alarm State Machine
│   ├── break_scheduler.py        # Pausentimer State Machine
│   ├── popup.py                  # Alarm-Popup
│   ├── break_popup.py            # Pausen-Popup
│   ├── settings_window.py        # Einstellungen-UI
│   ├── chrome_monitor.py         # Website/App-Erkennung (Windows API)
│   ├── foreground_tracker.py     # Zeit-Akkumulation für Trigger
│   ├── autostart.py              # Windows-Autostart
│   ├── theme.py                  # Design-Tokens
│   └── widgets.py                # Custom Widgets
├── Android/                      # Android (Kotlin/Compose)
│   ├── app/src/main/kotlin/com/stickyalarm/
│   │   ├── service/              # Foreground Service + Notifications
│   │   ├── domain/               # Scheduler, Tracker, Monitor
│   │   ├── data/                 # Config + DataStore
│   │   ├── ui/                   # Compose Screens + Theme
│   │   └── util/                 # Permissions, Package Utils
│   └── build.gradle.kts
├── assets/                       # Icons + Sounds
├── build.bat                     # Windows Build-Script
└── requirements.txt              # Python-Abhängigkeiten
```

## Wie es funktioniert

1. **Zeitfenster aktiv** — Alarm-Popup erscheint (z.B. ab 20:00)
2. **Schlummern** — Popup verschwindet für X Min, kommt dann zurück
3. **Bestätigen** — Popup verschwindet, App-Monitoring startet
4. **Trigger-Check** — Öffnest du eine Trigger-App, kommt der Alarm zurück
5. **Zeit-Trigger** — Bei Apps mit Zeitlimit zählt ein Session-Counter
6. **Zeitfenster endet** — Alarm stoppt automatisch (z.B. um 04:00)

## Tech Stack

| | Windows | Android |
|---|---|---|
| **Sprache** | Python 3 | Kotlin |
| **UI** | tkinter | Jetpack Compose + Material 3 |
| **App-Erkennung** | ctypes EnumWindows + psutil | UsageStatsManager |
| **Persistenz** | JSON (%APPDATA%) | DataStore + kotlinx.serialization |
| **Hintergrund** | pystray System Tray | Foreground Service |
| **Build** | PyInstaller | Gradle |

## Lizenz

[MIT](LICENSE)
