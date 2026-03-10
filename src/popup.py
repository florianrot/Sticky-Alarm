"""Unignorable alarm popup — fullscreen overlay or centered card with rounded corners."""
import tkinter as tk
import winsound
import os

import theme as T
from widgets import RoundedButton, fade_in_window, fade_out_window, round_rect


class AlarmPopup:
    def __init__(self, root, on_snooze, on_confirm,
                 sound_file="", popup_text="", title="Abendroutine",
                 snooze_label="Schlummern", confirm_label="Abendroutine starten",
                 fullscreen=True):
        self.root = root
        self.on_snooze = on_snooze
        self.on_confirm = on_confirm
        self.sound_file = sound_file
        self.popup_text = popup_text
        self.title = title
        self.snooze_label = snooze_label
        self.confirm_label = confirm_label
        self.fullscreen = fullscreen
        self.popup = None
        self._refocus_id = None
        self._pulse_id = None
        self._is_test = False
        self._icon_label = None

    def show(self, is_test=False):
        if self.popup and self.popup.winfo_exists():
            return
        self._is_test = is_test

        self.popup = tk.Toplevel(self.root)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)

        sx = self.popup.winfo_screenwidth()
        sy = self.popup.winfo_screenheight()

        cw, ch = 520, 420
        radius = T.CARD_RADIUS
        margin = 10

        if self.fullscreen:
            self.popup.geometry(f"{sx}x{sy}+0+0")
            self.popup.configure(bg="#000000")

            card_canvas = tk.Canvas(
                self.popup, width=cw + margin * 2, height=ch + margin * 2,
                bg="#000000", highlightthickness=0, bd=0)
            card_canvas.place(relx=0.5, rely=0.5, anchor="center")
        else:
            pw, ph = cw + margin * 2, ch + margin * 2
            x, y = (sx - pw) // 2, (sy - ph) // 2
            self.popup.geometry(f"{pw}x{ph}+{x}+{y}")
            self.popup.configure(bg="#FF00FF")
            self.popup.attributes("-transparentcolor", "#FF00FF")

            card_canvas = tk.Canvas(
                self.popup, width=pw, height=ph,
                bg="#FF00FF", highlightthickness=0, bd=0)
            card_canvas.pack(fill="both", expand=True)

        self.popup.protocol("WM_DELETE_WINDOW", lambda: None)
        self.popup.bind("<Alt-F4>", lambda e: "break")
        self.popup.bind("<Escape>", lambda e: "break")
        self.popup.bind("<Alt-Key>", lambda e: "break")

        # Shadow layer
        round_rect(card_canvas, margin + 4, margin + 4,
                   margin + cw + 4, margin + ch + 4,
                   radius=radius, fill=T.BG_SHADOW, outline="")
        # Card background
        round_rect(card_canvas, margin, margin,
                   margin + cw, margin + ch,
                   radius=radius, fill=T.BG, outline=T.BORDER)

        # Content frame
        inner = tk.Frame(card_canvas, bg=T.BG)
        card_canvas.create_window(
            margin + cw // 2, margin + ch // 2,
            window=inner, width=cw - 96, height=ch - 80)

        # Alarm icon (pulsing)
        self._icon_label = tk.Label(
            inner, text="\u23f0", font=("Segoe UI Emoji", 44),
            bg=T.BG, fg=T.ACCENT,
        )
        self._icon_label.pack(pady=(0, 10))

        # Title
        tk.Label(
            inner, text=self.title,
            font=(T.FONT, 28, "bold"), bg=T.BG, fg=T.TEXT,
        ).pack(pady=(0, 8))

        # Subtitle
        subtitle = self.popup_text or "Dein System hat heute geliefert.\nJetzt darf es sich erholen."
        tk.Label(
            inner, text=subtitle,
            font=(T.FONT, 12), bg=T.BG, fg=T.TEXT_MUTED,
            justify="center", wraplength=400,
        ).pack(pady=(0, 36))

        # Buttons
        btn_row = tk.Frame(inner, bg=T.BG)
        btn_row.pack(fill="x")

        RoundedButton(
            btn_row, text=self.snooze_label,
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._on_snooze,
            width=200, height=54, radius=22,
        ).pack(side="left")

        RoundedButton(
            btn_row, text=self.confirm_label,
            bg=T.ACCENT, fg=T.BG,
            hover_bg=T.ACCENT_HOVER, hover_fg=T.BG,
            command=self._on_confirm,
            width=220, height=54, radius=22,
            font=(T.FONT, T.FONT_SIZE_LG, "bold"),
        ).pack(side="right")

        fade_in_window(self.popup, duration_ms=350)
        self._play_sound()
        self._start_refocus()
        self._start_pulse()
        self.popup.focus_force()
        self.popup.grab_set()

    def _start_pulse(self):
        """Pulse the alarm icon between ACCENT and ACCENT_MUTED."""
        self._pulse_step = 0
        self._pulse_direction = 1
        self._pulse_tick()

    def _pulse_tick(self):
        if not self.popup or not self.popup.winfo_exists() or not self._icon_label:
            return
        steps = 20
        t = self._pulse_step / steps
        r1, g1, b1 = int(T.ACCENT[1:3], 16), int(T.ACCENT[3:5], 16), int(T.ACCENT[5:7], 16)
        r2, g2, b2 = int(T.ACCENT_MUTED[1:3], 16), int(T.ACCENT_MUTED[3:5], 16), int(T.ACCENT_MUTED[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        color = f"#{r:02x}{g:02x}{b:02x}"
        self._icon_label.configure(fg=color)

        self._pulse_step += self._pulse_direction
        if self._pulse_step >= steps:
            self._pulse_direction = -1
        elif self._pulse_step <= 0:
            self._pulse_direction = 1

        self._pulse_id = self.root.after(80, self._pulse_tick)

    def _stop_pulse(self):
        if self._pulse_id:
            self.root.after_cancel(self._pulse_id)
            self._pulse_id = None

    def _play_sound(self):
        try:
            if self.sound_file and os.path.isfile(self.sound_file):
                winsound.PlaySound(
                    self.sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            else:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

    def _stop_sound(self):
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

    def _start_refocus(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.attributes("-topmost", True)
            self.popup.focus_force()
            self.popup.lift()
            try:
                self.popup.grab_set()
            except Exception:
                pass
            self._refocus_id = self.root.after(2000, self._start_refocus)

    def _stop_refocus(self):
        if self._refocus_id:
            self.root.after_cancel(self._refocus_id)
            self._refocus_id = None

    def _on_snooze(self):
        self._fade_dismiss(self.on_snooze)

    def _on_confirm(self):
        self._fade_dismiss(self.on_confirm)

    def _fade_dismiss(self, callback):
        self._stop_refocus()
        self._stop_pulse()
        self._stop_sound()
        if self.popup and self.popup.winfo_exists():
            try:
                self.popup.grab_release()
            except Exception:
                pass
            fade_out_window(self.popup, duration_ms=250, on_done=lambda: self._destroy_and_call(callback))
        else:
            self.popup = None
            callback()

    def _destroy_and_call(self, callback):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        self.popup = None
        callback()

    def dismiss(self):
        self._stop_refocus()
        self._stop_pulse()
        self._stop_sound()
        if self.popup and self.popup.winfo_exists():
            try:
                self.popup.grab_release()
            except Exception:
                pass
            self.popup.destroy()
        self.popup = None

    @property
    def is_showing(self):
        return self.popup is not None and self.popup.winfo_exists()
