"""Scheduler with state machine for Sticky Alarm."""
from enum import Enum, auto
from datetime import datetime, timedelta


class State(Enum):
    WAITING = auto()
    ACTIVE = auto()
    SNOOZED = auto()
    CONFIRMED = auto()


class Scheduler:
    def __init__(self, config):
        self.config = config
        self.state = State.WAITING
        self._snooze_after = None
        self._was_in_window = self._is_in_window()

    def _is_in_window(self):
        now = datetime.now()
        return self.config.any_profile_active(now.hour, now.minute)

    def tick(self):
        now = datetime.now()
        in_window = self.config.any_profile_active(now.hour, now.minute)

        if not in_window:
            self.state = State.WAITING
            self._snooze_after = None
            self._was_in_window = False
            return self.state

        if self.state == State.WAITING:
            if self._was_in_window:
                self._was_in_window = False
                self.state = State.CONFIRMED
            else:
                self.state = State.ACTIVE
        elif self.state == State.SNOOZED:
            if self._snooze_after and now >= self._snooze_after:
                self.state = State.ACTIVE
                self._snooze_after = None

        return self.state

    def snooze(self, snooze_minutes=None):
        self.state = State.SNOOZED
        minutes = snooze_minutes or self.config.snooze_minutes
        self._snooze_after = datetime.now() + timedelta(minutes=minutes)

    def confirm_routine(self):
        self.state = State.CONFIRMED

    def trigger_detected(self):
        if self.state == State.CONFIRMED:
            self.state = State.ACTIVE

    def force_trigger(self):
        self.state = State.ACTIVE
