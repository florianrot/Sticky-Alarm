"""Foreground time tracker for time-based triggers."""
import time


class ForegroundTracker:
    def __init__(self):
        self._active = {}  # trigger_name -> accumulated_seconds
        self._last_update = {}  # trigger_name -> last_seen_timestamp

    def update_active_matches(self, matched_names: list):
        now = time.time()
        current = set(matched_names)

        for name in current:
            if name in self._last_update:
                delta = now - self._last_update[name]
                if delta < 15:  # Only count if seen recently (within tick interval)
                    self._active[name] = self._active.get(name, 0) + delta
            self._last_update[name] = now

        # Clear triggers that are no longer active
        for name in list(self._last_update):
            if name not in current:
                del self._last_update[name]

    def has_exceeded_limit(self, trigger) -> bool:
        if not trigger.is_time_based:
            return False
        accumulated = self._active.get(trigger.name, 0)
        return accumulated >= trigger.time_limit_minutes * 60

    def reset_trigger(self, name: str):
        self._active.pop(name, None)
        self._last_update.pop(name, None)

    def reset_all(self):
        self._active.clear()
        self._last_update.clear()
