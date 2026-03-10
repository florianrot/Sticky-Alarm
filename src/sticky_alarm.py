"""Sticky Alarm — main entry point."""
import sys
import os
import threading
import tkinter as tk
from datetime import datetime

from PIL import Image, ImageDraw, ImageTk
import pystray

from config import Config
from scheduler import Scheduler, State
from popup import AlarmPopup
from chrome_monitor import get_active_matches, close_trigger_apps, is_app_window_open
from foreground_tracker import ForegroundTracker
from settings_window import SettingsWindow
from break_scheduler import BreakScheduler, BreakState
from break_popup import BreakPopup


class StickyAlarmApp:
    def __init__(self):
        self.config = Config.load()
        self.scheduler = Scheduler(self.config)
        self.tracker = ForegroundTracker()
        self.root = tk.Tk()
        self.root.withdraw()

        self._icon_img = self._create_tray_image()
        self._icon_photo = ImageTk.PhotoImage(self._icon_img)
        self.root.iconphoto(True, self._icon_photo)

        self._active_profile = None
        self._matched_triggers = []

        self.popup = AlarmPopup(
            self.root,
            on_snooze=self._on_snooze,
            on_confirm=self._on_confirm,
            sound_file=self.config.sound_file,
            popup_text=self.config.popup_text,
            title=self.config.popup_title,
            snooze_label=self.config.snooze_label,
            confirm_label=self.config.confirm_label,
            fullscreen=self.config.fullscreen_popup,
        )
        self.break_scheduler = BreakScheduler(self.config)
        self.settings = SettingsWindow(
            self.root, self.config,
            on_save=self._on_settings_saved,
            on_test=self._on_test,
            break_scheduler=self.break_scheduler,
        )
        self.break_popup = BreakPopup(
            self.root,
            on_snooze=self._on_break_snooze,
            on_complete=self._on_break_complete,
        )
        self.tray_icon = None

    def run(self):
        threading.Thread(target=self._run_tray, daemon=True).start()
        self._schedule_tick()
        self.root.mainloop()

    def _create_tray_image(self):
        # Try loading from file first
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if not os.path.isfile(icon_path):
            # PyInstaller bundled path
            icon_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.isfile(icon_path):
            try:
                img = Image.open(icon_path).convert("RGBA")
                img = img.resize((64, 64), Image.LANCZOS)
                return img
            except Exception:
                pass
        # Fallback: clean geometric alarm clock
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Clock body (circle)
        draw.ellipse([10, 14, 54, 58], fill="#ffffff")
        # Bell top bumps
        draw.ellipse([18, 6, 30, 18], fill="#ffffff")
        draw.ellipse([34, 6, 46, 18], fill="#ffffff")
        # Clock face (dark circle inside)
        draw.ellipse([16, 20, 48, 52], fill="#1a1a1a")
        # Clock hands
        draw.line([32, 36, 32, 26], fill="#ffffff", width=2)
        draw.line([32, 36, 40, 36], fill="#ffffff", width=2)
        # Small dot at center
        draw.ellipse([30, 34, 34, 38], fill="#ffffff")
        return img

    def _run_tray(self):
        image = self._create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("Einstellungen", self._show_settings, default=True),
            pystray.MenuItem("Alarm testen", self._on_test),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Beenden", self._quit),
        )
        self.tray_icon = pystray.Icon("StickyAlarm", image, "Sticky Alarm", menu)
        self.tray_icon.run()

    def _show_settings(self, *_args):
        self.root.after(0, self.settings.show)

    def _schedule_tick(self):
        self._tick()
        self.root.after(5000, self._schedule_tick)

    def _tick(self):
        state = self.scheduler.tick()

        if state == State.ACTIVE and not self.popup.is_showing:
            self._apply_profile_to_popup(self._active_profile)
            self.popup.show()

        elif state == State.CONFIRMED:
            now = datetime.now()
            active_triggers = self.config.get_triggers_in_window(now.hour, now.minute)
            if active_triggers:
                matches = get_active_matches(active_triggers)
                if matches:
                    self.tracker.update_active_matches(matches)
                    matched_triggers = [t for t in active_triggers if t.name in matches]

                    # Check immediate triggers first
                    immediate = [t for t in matched_triggers if not t.is_time_based]
                    if immediate:
                        self._active_profile = self.config.get_profile_for_trigger(immediate[0])
                        self._matched_triggers = immediate
                        self.scheduler.trigger_detected()
                    else:
                        # Check time-based triggers
                        for trigger in matched_triggers:
                            if trigger.is_time_based and self.tracker.has_exceeded_limit(trigger):
                                self._active_profile = self.config.get_profile_for_trigger(trigger)
                                self._matched_triggers = [trigger]
                                self.scheduler.trigger_detected()
                                break
                else:
                    self.tracker.update_active_matches([])

        elif state == State.WAITING:
            if self.popup.is_showing:
                self.popup.dismiss()

        # Break timer (independent)
        break_state = self.break_scheduler.tick()
        if break_state == BreakState.BREAK_DUE and not self.break_popup.is_showing:
            if not self.popup.is_showing:
                self.break_scheduler.start_break()
                self.break_popup.show(
                    self.config.break_duration_minutes * 60,
                    title=self.config.break_popup_title,
                    text=self.config.break_popup_text,
                    fullscreen=self.config.break_fullscreen,
                    icon=self.config.break_icon)
        elif self.popup.is_showing and self.break_popup.is_showing:
            # Alarm takes priority — dismiss break
            self.break_popup.dismiss()
            self.break_scheduler.skip_break()

    def _apply_profile_to_popup(self, profile):
        if profile:
            self.popup.title = profile.alarm_title or self.config.popup_title
            self.popup.popup_text = profile.alarm_message or self.config.popup_text
            self.popup.snooze_label = profile.snooze_label or self.config.snooze_label
            self.popup.confirm_label = profile.confirm_label or self.config.confirm_label
        else:
            self.popup.title = self.config.popup_title
            self.popup.popup_text = self.config.popup_text
            self.popup.snooze_label = self.config.snooze_label
            self.popup.confirm_label = self.config.confirm_label
        self.popup.sound_file = self.config.sound_file
        self.popup.fullscreen = self.config.fullscreen_popup

    def _on_snooze(self):
        profile = self._active_profile or self.config.default_profile
        snooze_min = profile.snooze_minutes or self.config.snooze_minutes
        self.scheduler.snooze(snooze_min)

    def _on_confirm(self):
        self.scheduler.confirm_routine()
        # Close matched trigger apps (or scan now if first alarm)
        triggers_to_close = self._matched_triggers
        if not triggers_to_close:
            now = datetime.now()
            active_triggers = self.config.get_triggers_in_window(now.hour, now.minute)
            if active_triggers:
                matches = get_active_matches(active_triggers)
                triggers_to_close = [t for t in active_triggers if t.name in matches]
        if triggers_to_close:
            close_trigger_apps(triggers_to_close)
        for t in triggers_to_close:
            self.tracker.reset_trigger(t.name)
        # Launch profile apps
        self._launch_routine_apps()

    def _launch_routine_apps(self):
        profile = self._active_profile or self.config.default_profile
        for app_path in profile.launch_apps:
            if not app_path or not os.path.exists(app_path):
                continue
            app_name = os.path.splitext(os.path.basename(app_path))[0]
            if is_app_window_open(app_name):
                continue
            try:
                os.startfile(app_path)
            except Exception:
                pass

    def _on_test(self, *_args):
        def _trigger():
            self._active_profile = None
            self._matched_triggers = []
            self.scheduler.force_trigger()
            self._apply_profile_to_popup(None)
            self.popup.show(is_test=True)
        self.root.after(0, _trigger)

    def _on_break_snooze(self):
        self.break_scheduler.snooze()

    def _on_break_complete(self):
        self.break_scheduler.skip_break()

    def _on_settings_saved(self):
        self.scheduler.config = self.config
        self.break_scheduler.config = self.config
        self.break_scheduler.reload_config()

        # Re-lookup active profile from new config (old reference is stale)
        if self._active_profile:
            old_id = self._active_profile.id
            self._active_profile = None
            for p in self.config.schedule_profiles:
                if p.id == old_id:
                    self._active_profile = p
                    break

        # Update snooze duration if currently snoozed
        if self.scheduler.state == State.SNOOZED:
            profile = self._active_profile or self.config.default_profile
            new_snooze = profile.snooze_minutes or self.config.snooze_minutes
            self.scheduler.update_snooze_duration(new_snooze)

        self._apply_profile_to_popup(self._active_profile)

    def _quit(self, *_args):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.quit)


def main():
    import socket
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock_socket.bind(("127.0.0.1", 59173))
    except socket.error:
        sys.exit(0)
    app = StickyAlarmApp()
    app.run()


if __name__ == "__main__":
    main()
