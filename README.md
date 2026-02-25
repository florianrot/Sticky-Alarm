# Sticky Alarm

**ADHS-freundlicher Abendroutine-Trigger für Windows.**

Sticky Alarm erinnert dich jeden Abend daran, deine Abendroutine zu starten — und bleibt so lange hartnäckig, bis du es tust. Perfekt für alle, die abends in YouTube, Reddit & Co. versinken und das Schlafen vergessen.

## Features

- **Alarm-Popup** — Fullscreen-Overlay oder zentrierte Karte, nicht ignorierbar
- **Schlummern** — Konfigurierbarer Snooze (Standard: 15 Min)
- **Website-Trigger** — Erkennt automatisch ob ablenkende Seiten (YouTube, Instagram, Reddit, ...) im Browser geöffnet sind und löst den Alarm erneut aus
- **App-Trigger** — Überwacht laufende Prozesse (z.B. Spiele) als zusätzliche Trigger
- **Auto-Start Apps** — Startet automatisch konfigurierte Apps (z.B. Brain.fm, Tana) wenn du die Abendroutine bestätigst
- **Individuelle Sounds** — Windows .wav Dateien als Alarm-Sound
- **System Tray** — Läuft unauffällig im Hintergrund
- **Windows Autostart** — Optional beim Hochfahren starten
- **Dark Theme** — Apple-inspiriertes, minimalistisches Design

## Installation

### Voraussetzungen

- Python 3.10+
- Windows 10/11

### Setup

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# App starten
python src/sticky_alarm.py
```

### Als .exe bauen

```bash
# Build-Script ausführen
build.bat
```

Die fertige `StickyAlarm.exe` liegt danach in `dist/`.

## Projektstruktur

```
Sticky_Alarm/
├── src/                         # Quellcode
│   ├── sticky_alarm.py          # Main Entry Point + App-Logik
│   ├── config.py                # Konfiguration (JSON-Persistenz)
│   ├── scheduler.py             # State Machine (WAITING → ACTIVE → SNOOZED/CONFIRMED)
│   ├── popup.py                 # Alarm-Popup (Fullscreen/Karte)
│   ├── settings_window.py       # Einstellungen-UI
│   ├── chrome_monitor.py        # Website- & App-Erkennung (Windows API)
│   ├── autostart.py             # Windows-Autostart Verwaltung
│   ├── theme.py                 # Design-Tokens (Dark Theme)
│   └── widgets.py               # Custom Widgets (Rounded Buttons, Inputs, etc.)
├── assets/
│   └── icon.ico                 # App-Icon
├── tools/
│   └── create_icon.py           # Icon-Generator (Entwickler-Tool)
├── build.bat                    # PyInstaller Build-Script
├── requirements.txt             # Python-Abhängigkeiten
├── .gitignore
└── README.md
```

## Konfiguration

Die Einstellungen werden unter `%APPDATA%/StickyAlarm/config.json` gespeichert:

| Einstellung | Standard | Beschreibung |
|---|---|---|
| Alarmzeit | 20:00 | Ab wann der Alarm aktiv wird |
| Ende | 04:00 | Bis wann der Alarm aktiv ist |
| Snooze | 15 Min | Schlummer-Dauer |
| Website-Trigger | YouTube, Instagram, Reddit, ... | Browser-Tabs die den Alarm erneut auslösen |
| App-Trigger | *(leer)* | Prozesse die den Alarm erneut auslösen |
| Auto-Start Apps | *(leer)* | Apps die bei Routinestart geöffnet werden |
| Fullscreen | An | Fullscreen-Overlay statt kleiner Karte |

## Wie es funktioniert

1. **20:00** — Alarm-Popup erscheint
2. **Schlummern** — Popup verschwindet für 15 Min, kommt dann zurück
3. **Abendroutine starten** — Popup verschwindet, konfigurierte Apps werden gestartet
4. **Trigger-Check** — Wenn du danach YouTube etc. öffnest, kommt der Alarm sofort wieder
5. **04:00** — Alarm-Fenster schließt sich automatisch

## Tech Stack

- **Python 3** + **tkinter** (GUI)
- **pystray** + **Pillow** (System Tray)
- **psutil** (Prozessüberwachung)
- **ctypes** / Windows API (Fenstertitel-Erkennung)
- **PyInstaller** (Standalone .exe)

## Lizenz

MIT
