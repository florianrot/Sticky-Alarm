"""Sticky Alarm — Abendroutine-Trigger. Main entry point."""

import sys
import os
import threading
import tkinter as tk

from PIL import Image, ImageDraw, ImageTk
import pystray

from config import Config
from scheduler import Scheduler, State
from popup import AlarmPopup
from chrome_monitor import is_trigger_app_running, is_trigger_site_open, is_app_window_open
from settings_window import SettingsWindow


class StickyAlarmApp:
    def __init__(self):
        self.config = Config.load()
        self.scheduler = Scheduler(self.config)
        self.root = tk.Tk()
        self.root.withdraw()  # Hidden main window

        # Set window icon for all Toplevels (taskbar, title bar)
        self._icon_img = self._create_tray_image()
        self._icon_photo = ImageTk.PhotoImage(self._icon_img)
        self.root.iconphoto(True, self._icon_photo)

        self.popup = AlarmPopup(
            self.root,
            on_snooze=self._on_snooze,
            on_confirm=self._on_confirm,
            sound_file=self.config.sound_file,
            popup_text=self.config.popup_text,
            fullscreen=self.config.fullscreen_popup,
        )
        self.settings = SettingsWindow(
            self.root, self.config,
            on_save=self._on_settings_saved,
            on_test=self._on_test,
        )
        self.tray_icon = None
        self._prev_state = None

    def run(self):
        # Start tray icon in background thread
        threading.Thread(target=self._run_tray, daemon=True).start()

        # Start main loop with periodic checks
        self._schedule_tick()
        self.root.mainloop()

    # --- Tray Icon ---

    def _create_tray_image(self):
        """Create a white alarm clock icon for system tray."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Clock body — white
        draw.ellipse([8, 12, 56, 60], fill="#ffffff")
        # Bell top — white
        draw.polygon([(22, 14), (32, 4), (42, 14)], fill="#ffffff")
        # Clock hands — dark
        draw.line([32, 36, 32, 22], fill="#1a1a1a", width=3)
        draw.line([32, 36, 42, 36], fill="#1a1a1a", width=2)
        return img

    def _run_tray(self):
        image = self._create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("Einstellungen", self._show_settings),
            pystray.MenuItem("Alarm testen", self._on_test),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Beenden", self._quit),
        )
        self.tray_icon = pystray.Icon("StickyAlarm", image, "Sticky Alarm", menu)
        self.tray_icon.run()

    def _show_settings(self, *_args):
        self.root.after(0, self.settings.show)

    # --- Main tick loop (runs on tkinter main thread via after()) ---

    def _schedule_tick(self):
        self._tick()
        self.root.after(5000, self._schedule_tick)  # every 5 seconds

    def _tick(self):
        state = self.scheduler.tick()

        if state == State.ACTIVE and not self.popup.is_showing:
            self.popup.sound_file = self.config.sound_file
            self.popup.fullscreen = self.config.fullscreen_popup
            self.popup.show()

        elif state == State.CONFIRMED:
            # Check for trigger websites (Chrome/Edge window titles)
            # and trigger apps (non-browser processes)
            if (is_trigger_site_open(self.config.trigger_sites)
                    or is_trigger_app_running(self.config.trigger_apps)):
                self.scheduler.chrome_detected()
                # Next tick will show popup

        elif state == State.WAITING:
            if self.popup.is_showing:
                self.popup.dismiss()

    # --- Callbacks ---

    def _on_snooze(self):
        self.scheduler.snooze()

    def _on_confirm(self):
        self.scheduler.confirm_routine()
        self._launch_routine_apps()

    def _launch_routine_apps(self):
        """Launch configured apps, skipping those already running."""
        for app_path in self.config.launch_apps:
            if not os.path.exists(app_path):
                continue
            # Check if app is likely already open by window title
            app_name = os.path.splitext(os.path.basename(app_path))[0]
            if is_app_window_open(app_name):
                continue
            try:
                os.startfile(app_path)
            except Exception:
                pass

    def _on_test(self, *_args):
        def _trigger():
            self.scheduler.force_trigger()
            self.popup.sound_file = self.config.sound_file
            self.popup.popup_text = self.config.popup_text
            self.popup.fullscreen = self.config.fullscreen_popup
            self.popup.show()
        self.root.after(0, _trigger)

    def _on_settings_saved(self):
        # Reload config into scheduler and popup
        self.scheduler.config = self.config
        self.popup.sound_file = self.config.sound_file
        self.popup.popup_text = self.config.popup_text
        self.popup.fullscreen = self.config.fullscreen_popup

    def _quit(self, *_args):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.quit)


def main():
    # Prevent multiple instances
    import socket
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock_socket.bind(("127.0.0.1", 59173))
    except socket.error:
        sys.exit(0)  # Already running

    app = StickyAlarmApp()
    app.run()


if __name__ == "__main__":
    main()
