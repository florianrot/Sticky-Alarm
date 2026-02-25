# Sticky Alarm

**ADHS-freundlicher Abendroutine-Trigger f\u00fcr Windows.**

Sticky Alarm erinnert dich jeden Abend daran, deine Abendroutine zu starten \u2014 und bleibt so lange hartn\u00e4ckig, bis du es tust. Perfekt f\u00fcr alle, die abends in YouTube, Reddit & Co. versinken und das Schlafen vergessen.

## Features

- **Alarm-Popup** \u2014 Fullscreen-Overlay oder zentrierte Karte, nicht ignorierbar
- **Schlummern** \u2014 Konfigurierbarer Snooze (Standard: 15 Min)
- **Website-Trigger** \u2014 Erkennt automatisch ob ablenkende Seiten (YouTube, Instagram, Reddit, ...) im Browser ge\u00f6ffnet sind und l\u00f6st den Alarm erneut aus
- **App-Trigger** \u2014 \u00dcberwacht laufende Prozesse (z.B. Spiele) als zus\u00e4tzliche Trigger
- **Auto-Start Apps** \u2014 Startet automatisch konfigurierte Apps (z.B. Brain.fm, Tana) wenn du die Abendroutine best\u00e4tigst
- **Individuelle Sounds** \u2014 Windows .wav Dateien als Alarm-Sound
- **System Tray** \u2014 L\u00e4uft unauff\u00e4llig im Hintergrund
- **Windows Autostart** \u2014 Optional beim Hochfahren starten
- **Dark Theme** \u2014 Apple-inspiriertes, minimalistisches Design

## Screenshot

*Coming soon*

## Installation

### Voraussetzungen

- Python 3.10+
- Windows 10/11

### Setup

```bash
# Abh\u00e4ngigkeiten installieren
pip install -r requirements.txt

# App starten
python sticky_alarm.py
```

### Als .exe bauen

```bash
# Build-Script ausf\u00fchren
build.bat
```

Die fertige `StickyAlarm.exe` liegt danach in `dist/`.

## Projektstruktur

```
Sticky_Alarm/
\u251c\u2500\u2500 sticky_alarm.py      # Main Entry Point + App-Logik
\u251c\u2500\u2500 config.py            # Konfiguration (JSON-Persistenz)
\u251c\u2500\u2500 scheduler.py         # State Machine (WAITING \u2192 ACTIVE \u2192 SNOOZED/CONFIRMED)
\u251c\u2500\u2500 popup.py             # Alarm-Popup (Fullscreen/Karte)
\u251c\u2500\u2500 settings_window.py   # Einstellungen-UI
\u251c\u2500\u2500 chrome_monitor.py    # Website- & App-Erkennung (Windows API)
\u251c\u2500\u2500 autostart.py         # Windows-Autostart Verwaltung
\u251c\u2500\u2500 theme.py             # Design-Tokens (Dark Theme)
\u251c\u2500\u2500 widgets.py           # Custom Widgets (Rounded Buttons, Inputs, etc.)
\u251c\u2500\u2500 icon.ico             # App-Icon
\u251c\u2500\u2500 build.bat            # PyInstaller Build-Script
\u251c\u2500\u2500 requirements.txt     # Python-Abh\u00e4ngigkeiten
\u2514\u2500\u2500 tools/
    \u2514\u2500\u2500 create_icon.py   # Icon-Generator (Entwickler-Tool)
```

## Konfiguration

Die Einstellungen werden unter `%APPDATA%/StickyAlarm/config.json` gespeichert:

| Einstellung | Standard | Beschreibung |
|---|---|---|
| Alarmzeit | 20:00 | Ab wann der Alarm aktiv wird |
| Ende | 04:00 | Bis wann der Alarm aktiv ist |
| Snooze | 15 Min | Schlummer-Dauer |
| Website-Trigger | YouTube, Instagram, Reddit, ... | Browser-Tabs die den Alarm erneut ausl\u00f6sen |
| App-Trigger | *(leer)* | Prozesse die den Alarm erneut ausl\u00f6sen |
| Auto-Start Apps | *(leer)* | Apps die bei Routinestart ge\u00f6ffnet werden |
| Fullscreen | An | Fullscreen-Overlay statt kleiner Karte |

## Wie es funktioniert

1. **20:00** \u2014 Alarm-Popup erscheint
2. **Schlummern** \u2014 Popup verschwindet f\u00fcr 15 Min, kommt dann zur\u00fcck
3. **Abendroutine starten** \u2014 Popup verschwindet, konfigurierte Apps werden gestartet
4. **Trigger-Check** \u2014 Wenn du danach YouTube etc. \u00f6ffnest, kommt der Alarm sofort wieder
5. **04:00** \u2014 Alarm-Fenster schlie\u00dft sich automatisch

## Tech Stack

- **Python 3** + **tkinter** (GUI)
- **pystray** + **Pillow** (System Tray)
- **psutil** (Prozess\u00fcberwachung)
- **ctypes** / Windows API (Fenstertitel-Erkennung)
- **PyInstaller** (Standalone .exe)

## Lizenz

MIT
