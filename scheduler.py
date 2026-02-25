"""Scheduler with state machine for Sticky Alarm."""

from enum import Enum, auto
from datetime import datetime


class State(Enum):
    WAITING = auto()    # Outside active window, idle
    ACTIVE = auto()     # Popup should be shown
    SNOOZED = auto()    # User snoozed, waiting for timer
    CONFIRMED = auto()  # User confirmed routine, chrome monitor active


class Scheduler:
    def __init__(self, config):
        self.config = config
        self.state = State.WAITING
        self._snooze_after = None  # datetime when snooze expires
        self._was_in_window = self.is_in_active_window()  # suppress popup on startup

    def is_in_active_window(self, now: datetime = None) -> bool:
        now = now or datetime.now()
        current = now.hour * 60 + now.minute
        start = self.config.start_hour * 60 + self.config.start_minute
        end = self.config.end_hour * 60 + self.config.end_minute

        if start <= end:
            # Same-day window (e.g., 08:00 - 16:00)
            return start <= current < end
        else:
            # Overnight window (e.g., 20:00 - 04:00)
            return current >= start or current < end

    def tick(self) -> State:
        """Called periodically. Returns the current state after evaluation."""
        now = datetime.now()

        in_window = self.is_in_active_window(now)

        if not in_window:
            # Outside active window — reset
            self.state = State.WAITING
            self._snooze_after = None
            self._was_in_window = False
            return self.state

        if self.state == State.WAITING:
            if self._was_in_window:
                # App started mid-window — stay silent, don't show popup
                self._was_in_window = False
                self.state = State.CONFIRMED
            else:
                # Fresh entry into active window — trigger alarm
                self.state = State.ACTIVE
        elif self.state == State.SNOOZED:
            if self._snooze_after and now >= self._snooze_after:
                self.state = State.ACTIVE
                self._snooze_after = None
        # ACTIVE and CONFIRMED states stay as-is until explicitly changed

        return self.state

    def snooze(self):
        from datetime import timedelta
        self.state = State.SNOOZED
        self._snooze_after = datetime.now() + timedelta(minutes=self.config.snooze_minutes)

    def confirm_routine(self):
        self.state = State.CONFIRMED

    def chrome_detected(self):
        """Chrome was opened after confirmation — go back to ACTIVE."""
        if self.state == State.CONFIRMED:
            self.state = State.ACTIVE

    def force_trigger(self):
        """For testing: force popup regardless of time."""
        self.state = State.ACTIVE
