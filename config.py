"""Configuration management for Sticky Alarm."""

import json
import os
from dataclasses import dataclass, field, asdict


CONFIG_DIR = os.path.join(os.environ.get("APPDATA", ""), "StickyAlarm")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


@dataclass
class Config:
    start_hour: int = 20
    start_minute: int = 0
    end_hour: int = 4
    end_minute: int = 0
    snooze_minutes: int = 15
    sound_file: str = ""  # empty = first alarm sound from Windows\Media
    autostart: bool = False
    popup_text: str = "Dein System hat heute geliefert.\nJetzt darf es sich erholen."
    fullscreen_popup: bool = True
    trigger_apps: list = field(default_factory=list)
    trigger_sites: list = field(default_factory=lambda: [
        "youtube", "instagram", "reddit", "twitter",
        "tiktok", "facebook", "twitch",
    ])
    launch_apps: list = field(default_factory=list)
    custom_sounds: list = field(default_factory=list)

    def save(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> "Config":
        if not os.path.exists(CONFIG_FILE):
            config = cls()
            config.save()
            return config
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except (json.JSONDecodeError, TypeError):
            return cls()
