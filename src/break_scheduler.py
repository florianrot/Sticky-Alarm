"""Break timer scheduler — independent periodic break reminders."""
from enum import Enum, auto
from datetime import datetime, timedelta


class BreakState(Enum):
    IDLE = auto()        # disabled
    RUNNING = auto()     # counting toward next break
    BREAK_DUE = auto()   # interval elapsed, show popup
    BREAK_ACTIVE = auto()  # break popup showing, countdown running
    SNOOZED = auto()     # user snoozed, waiting


class BreakScheduler:
    def __init__(self, config):
        self.config = config
        self.state = BreakState.IDLE
        self._next_break = None
        self._break_end = None
        self._snooze_end = None
        self._timer_start = None
        self._last_tick_time = datetime.now()
        if config.break_enabled:
            self._reset_timer()

    def _reset_timer(self):
        now = datetime.now()
        self._timer_start = now
        self._next_break = now + timedelta(
            minutes=self.config.break_interval_minutes)
        self._break_end = None
        self._snooze_end = None
        self._last_tick_time = now
        self.state = BreakState.RUNNING

    def tick(self) -> BreakState:
        if not self.config.break_enabled:
            self.state = BreakState.IDLE
            return self.state

        now = datetime.now()

        # Detect PC lock/sleep: if gap between ticks >= 5 minutes, reset timer
        if self._last_tick_time:
            gap = (now - self._last_tick_time).total_seconds()
            if gap >= 300:  # 5 minutes
                self._last_tick_time = now
                self._reset_timer()
                return self.state
        self._last_tick_time = now

        if self.state == BreakState.IDLE:
            self._reset_timer()

        elif self.state == BreakState.RUNNING:
            if self._next_break and now >= self._next_break:
                self.state = BreakState.BREAK_DUE

        elif self.state == BreakState.BREAK_ACTIVE:
            if self._break_end and now >= self._break_end:
                self._reset_timer()

        elif self.state == BreakState.SNOOZED:
            if self._snooze_end and now >= self._snooze_end:
                self.state = BreakState.BREAK_DUE

        return self.state

    def start_break(self):
        self.state = BreakState.BREAK_ACTIVE
        self._break_end = datetime.now() + timedelta(
            minutes=self.config.break_duration_minutes)

    def snooze(self):
        self.state = BreakState.SNOOZED
        self._snooze_end = datetime.now() + timedelta(
            minutes=self.config.break_snooze_minutes)

    def skip_break(self):
        self._reset_timer()

    def remaining_break_seconds(self) -> int:
        if self.state == BreakState.BREAK_ACTIVE and self._break_end:
            return max(0, int((self._break_end - datetime.now()).total_seconds()))
        return 0

    def remaining_until_break_seconds(self) -> int:
        """Seconds until next break is due (for display in settings)."""
        if self.state == BreakState.RUNNING and self._next_break:
            return max(0, int((self._next_break - datetime.now()).total_seconds()))
        if self.state == BreakState.SNOOZED and self._snooze_end:
            return max(0, int((self._snooze_end - datetime.now()).total_seconds()))
        return 0

    def reload_config(self):
        if not self.config.break_enabled:
            self.state = BreakState.IDLE
            self._next_break = None
            self._break_end = None
            self._snooze_end = None
            self._timer_start = None
        elif self.state == BreakState.RUNNING and self._timer_start:
            # Smart adjust: keep elapsed time, recalculate next break
            elapsed = (datetime.now() - self._timer_start).total_seconds()
            new_interval_secs = self.config.break_interval_minutes * 60
            remaining = new_interval_secs - elapsed
            if remaining <= 0:
                # Elapsed already exceeds new interval — trigger soon
                self._next_break = datetime.now() + timedelta(seconds=5)
            else:
                self._next_break = datetime.now() + timedelta(seconds=remaining)
        elif self.state == BreakState.SNOOZED:
            # Re-apply snooze with new config snooze duration
            # Keep existing snooze_end, don't reset
            pass
        elif self.state in (BreakState.BREAK_DUE, BreakState.BREAK_ACTIVE):
            # Don't interrupt an active or due break
            pass
        elif self.state == BreakState.IDLE:
            self._reset_timer()
