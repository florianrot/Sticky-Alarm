"""Configuration management for Sticky Alarm (Windows-only)."""

import json
import os
import time
import random
from dataclasses import dataclass, field, asdict


CONFIG_DIR = os.path.join(os.environ.get("APPDATA", ""), "StickyAlarm")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def _generate_id():
    return f"{int(time.time() * 1000)}_{random.randint(0, 9999)}"


@dataclass
class TriggerSchedule:
    start_hour: int = 20
    start_minute: int = 0
    end_hour: int = 4
    end_minute: int = 0

    def is_in_window(self, hour, minute) -> bool:
        start = self.start_hour * 60 + self.start_minute
        end = self.end_hour * 60 + self.end_minute
        now = hour * 60 + minute
        if start <= end:
            return start <= now < end
        else:
            return now >= start or now < end

    @property
    def display(self):
        return (
            f"{self.start_hour:02d}:{self.start_minute:02d} - "
            f"{self.end_hour:02d}:{self.end_minute:02d}"
        )


@dataclass
class ScheduleProfile:
    id: str = ""
    name: str = "Abends"
    schedule: TriggerSchedule = None
    snooze_minutes: int = 0
    alarm_title: str = ""
    alarm_message: str = ""
    snooze_label: str = ""
    confirm_label: str = ""
    launch_apps: list = None

    def __post_init__(self):
        if not self.id:
            self.id = _generate_id()
        if self.schedule is None:
            self.schedule = TriggerSchedule()
        elif isinstance(self.schedule, dict):
            self.schedule = TriggerSchedule(**self.schedule)
        if self.launch_apps is None:
            self.launch_apps = []

    def to_dict(self):
        d = {
            "id": self.id,
            "name": self.name,
            "schedule": asdict(self.schedule),
        }
        if self.snooze_minutes:
            d["snooze_minutes"] = self.snooze_minutes
        if self.alarm_title:
            d["alarm_title"] = self.alarm_title
        if self.alarm_message:
            d["alarm_message"] = self.alarm_message
        if self.snooze_label:
            d["snooze_label"] = self.snooze_label
        if self.confirm_label:
            d["confirm_label"] = self.confirm_label
        if self.launch_apps:
            d["launch_apps"] = self.launch_apps
        return d

    @classmethod
    def from_dict(cls, d):
        schedule = d.get("schedule")
        if isinstance(schedule, dict):
            schedule = TriggerSchedule(**schedule)
        return cls(
            id=d.get("id", ""),
            name=d.get("name", "Abends"),
            schedule=schedule,
            snooze_minutes=d.get("snooze_minutes", 0),
            alarm_title=d.get("alarm_title", ""),
            alarm_message=d.get("alarm_message", ""),
            snooze_label=d.get("snooze_label", ""),
            confirm_label=d.get("confirm_label", ""),
            launch_apps=d.get("launch_apps", []),
        )


@dataclass
class TriggerEntry:
    name: str = ""
    type: str = "site"
    profile_id: str = ""
    time_limit_minutes: int = 0

    @property
    def is_time_based(self):
        return self.time_limit_minutes > 0

    def to_dict(self):
        d = {"name": self.name, "type": self.type}
        if self.profile_id:
            d["profile_id"] = self.profile_id
        if self.time_limit_minutes:
            d["time_limit_minutes"] = self.time_limit_minutes
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(
            name=d.get("name", ""),
            type=d.get("type", "site"),
            profile_id=d.get("profile_id", ""),
            time_limit_minutes=d.get("time_limit_minutes", 0),
        )


@dataclass
class Config:
    schedule_profiles: list = None
    triggers: list = None
    snooze_minutes: int = 15
    sound_file: str = ""
    autostart: bool = False
    popup_title: str = "Alarm"
    popup_text: str = "Dein System hat heute geliefert.\nJetzt darf es sich erholen."
    snooze_label: str = "Schlummern"
    confirm_label: str = "Abendroutine starten"
    fullscreen_popup: bool = True
    custom_sounds: list = None

    def __post_init__(self):
        if self.schedule_profiles is None:
            self.schedule_profiles = [
                ScheduleProfile(id="default", name="Abends")
            ]
        if self.triggers is None:
            self.triggers = [
                TriggerEntry(name="youtube.com", type="site", profile_id="default"),
                TriggerEntry(name="instagram.com", type="site", profile_id="default"),
                TriggerEntry(name="reddit.com", type="site", profile_id="default"),
                TriggerEntry(name="twitter.com", type="site", profile_id="default"),
                TriggerEntry(name="tiktok.com", type="site", profile_id="default"),
                TriggerEntry(name="facebook.com", type="site", profile_id="default"),
                TriggerEntry(name="twitch.tv", type="site", profile_id="default"),
            ]
        if self.custom_sounds is None:
            self.custom_sounds = []

    @property
    def default_profile(self):
        return self.schedule_profiles[0]

    def get_profile_for_trigger(self, trigger):
        if trigger.profile_id:
            for profile in self.schedule_profiles:
                if profile.id == trigger.profile_id:
                    return profile
        return self.default_profile

    def get_triggers_for_profile(self, profile_id):
        return [t for t in self.triggers if t.profile_id == profile_id
                or (not t.profile_id and profile_id == self.default_profile.id)]

    def get_snooze_for_profile(self, profile):
        return profile.snooze_minutes or self.snooze_minutes

    def get_triggers_in_window(self, hour, minute):
        result = []
        for trigger in self.triggers:
            profile = self.get_profile_for_trigger(trigger)
            if profile.schedule.is_in_window(hour, minute):
                result.append(trigger)
        return result

    def any_profile_active(self, hour, minute):
        for profile in self.schedule_profiles:
            if profile.schedule.is_in_window(hour, minute):
                return True
        return False

    def to_dict(self):
        return {
            "schedule_profiles": [p.to_dict() for p in self.schedule_profiles],
            "triggers": [t.to_dict() for t in self.triggers],
            "snooze_minutes": self.snooze_minutes,
            "sound_file": self.sound_file,
            "autostart": self.autostart,
            "popup_title": self.popup_title,
            "popup_text": self.popup_text,
            "snooze_label": self.snooze_label,
            "confirm_label": self.confirm_label,
            "fullscreen_popup": self.fullscreen_popup,
            "custom_sounds": self.custom_sounds,
        }

    def save(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls):
        if not os.path.exists(CONFIG_FILE):
            return cls()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return cls()
        if "schedule_profiles" in data:
            return cls._from_dict(data)
        return cls._migrate_old(data)

    @classmethod
    def _from_dict(cls, data):
        profiles = [
            ScheduleProfile.from_dict(p)
            for p in data.get("schedule_profiles", [])
        ]
        triggers = [
            TriggerEntry.from_dict(t)
            for t in data.get("triggers", [])
        ]
        # Migration: assign unlinked triggers to default profile
        if profiles:
            default_id = profiles[0].id
            for t in triggers:
                if not t.profile_id:
                    t.profile_id = default_id
        return cls(
            schedule_profiles=profiles or None,
            triggers=triggers or None,
            snooze_minutes=data.get("snooze_minutes", 15),
            sound_file=data.get("sound_file", ""),
            autostart=data.get("autostart", False),
            popup_title=data.get("popup_title", "Alarm"),
            popup_text=data.get("popup_text", "Dein System hat heute geliefert.\nJetzt darf es sich erholen."),
            snooze_label=data.get("snooze_label", "Schlummern"),
            confirm_label=data.get("confirm_label", "Abendroutine starten"),
            fullscreen_popup=data.get("fullscreen_popup", True),
            custom_sounds=data.get("custom_sounds", []),
        )

    @classmethod
    def _migrate_old(cls, data):
        schedule = TriggerSchedule(
            start_hour=data.get("start_hour", 20),
            start_minute=data.get("start_minute", 0),
            end_hour=data.get("end_hour", 4),
            end_minute=data.get("end_minute", 0),
        )
        profile = ScheduleProfile(
            id="default",
            name="Abends",
            schedule=schedule,
            launch_apps=data.get("launch_apps", []),
        )
        triggers = []
        for site in data.get("trigger_sites", []):
            triggers.append(TriggerEntry(name=site, type="site", profile_id="default"))
        for app in data.get("trigger_apps", []):
            triggers.append(TriggerEntry(name=app, type="app", profile_id="default"))
        config = cls(
            schedule_profiles=[profile],
            triggers=triggers or None,
            snooze_minutes=data.get("snooze_minutes", 15),
            sound_file=data.get("sound_file", ""),
            autostart=data.get("autostart", False),
            popup_title=data.get("popup_title", "Alarm"),
            popup_text=data.get("popup_text", "Dein System hat heute geliefert.\nJetzt darf es sich erholen."),
            snooze_label=data.get("snooze_label", "Schlummern"),
            confirm_label=data.get("confirm_label", "Abendroutine starten"),
            fullscreen_popup=data.get("fullscreen_popup", True),
            custom_sounds=data.get("custom_sounds", []),
        )
        config.save()
        return config
