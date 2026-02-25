"""Unignorable alarm popup — fullscreen overlay or centered card."""

import tkinter as tk
import winsound
import os

import theme as T
from widgets import RoundedButton, fade_in_window


class AlarmPopup:
    def __init__(self, root: tk.Tk, on_snooze, on_confirm,
                 sound_file: str = "", popup_text: str = "",
                 fullscreen: bool = True):
        self.root = root
        self.on_snooze = on_snooze
        self.on_confirm = on_confirm
        self.sound_file = sound_file
        self.popup_text = popup_text
        self.fullscreen = fullscreen
        self.popup = None
        self._refocus_id = None

    def show(self):
        if self.popup and self.popup.winfo_exists():
            return

        self.popup = tk.Toplevel(self.root)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)

        sx = self.popup.winfo_screenwidth()
        sy = self.popup.winfo_screenheight()

        if self.fullscreen:
            # Cover entire screen — no way to click beside it
            self.popup.geometry(f"{sx}x{sy}+0+0")
            self.popup.configure(bg="#000000")
        else:
            w, h = 520, 420
            x = (sx - w) // 2
            y = (sy - h) // 2
            self.popup.geometry(f"{w}x{h}+{x}+{y}")
            self.popup.configure(bg=T.BG, highlightbackground="#252525",
                                 highlightthickness=1)

        # Prevent closing
        self.popup.protocol("WM_DELETE_WINDOW", lambda: None)
        self.popup.bind("<Alt-F4>", lambda e: "break")
        self.popup.bind("<Escape>", lambda e: "break")
        self.popup.bind("<Alt-Key>", lambda e: "break")

        # Content card — centered on screen
        if self.fullscreen:
            # Semi-transparent dark overlay with centered card
            card = tk.Frame(self.popup, bg=T.BG, highlightbackground="#252525",
                            highlightthickness=1)
            card.place(relx=0.5, rely=0.5, anchor="center",
                       width=520, height=420)
        else:
            card = self.popup

        inner = tk.Frame(card, bg=T.BG)
        inner.pack(expand=True, fill="both", padx=48, pady=(44, 52))

        # Alarm icon — white
        tk.Label(
            inner, text="\u23f0", font=("Segoe UI Emoji", 44),
            bg=T.BG, fg=T.TEXT,
        ).pack(pady=(0, 10))

        # Title
        tk.Label(
            inner, text="Abendroutine",
            font=(T.FONT, 28, "bold"), bg=T.BG, fg=T.TEXT,
        ).pack(pady=(0, 8))

        # Configurable subtitle
        subtitle = self.popup_text or "Dein System hat heute geliefert.\nJetzt darf es sich erholen."
        tk.Label(
            inner, text=subtitle,
            font=(T.FONT, 12), bg=T.BG, fg=T.TEXT_MUTED,
            justify="center", wraplength=400,
        ).pack(pady=(0, 36))

        # Buttons
        btn_row = tk.Frame(inner, bg=T.BG)
        btn_row.pack(fill="x")

        snooze_btn = RoundedButton(
            btn_row, text="Schlummern",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._on_snooze,
            width=200, height=54, radius=16,
        )
        snooze_btn.pack(side="left")

        confirm_btn = RoundedButton(
            btn_row, text="Abendroutine starten",
            bg=T.BG_INPUT, fg=T.TEXT,
            hover_bg=T.BG_HOVER, hover_fg=T.ACCENT,
            command=self._on_confirm,
            width=220, height=54, radius=16,
            font=(T.FONT, T.FONT_SIZE_LG, "bold"),
        )
        confirm_btn.pack(side="right")

        # Fade-in animation
        fade_in_window(self.popup, duration_ms=350)

        # Sound
        self._play_sound()
        self._start_refocus()

        self.popup.focus_force()
        self.popup.grab_set()

    def _play_sound(self):
        try:
            if self.sound_file and os.path.isfile(self.sound_file):
                winsound.PlaySound(
                    self.sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
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
        self.dismiss()
        self.on_snooze()

    def _on_confirm(self):
        self.dismiss()
        self.on_confirm()

    def dismiss(self):
        self._stop_refocus()
        if self.popup and self.popup.winfo_exists():
            try:
                self.popup.grab_release()
            except Exception:
                pass
            self.popup.destroy()
        self.popup = None

    @property
    def is_showing(self) -> bool:
        return self.popup is not None and self.popup.winfo_exists()
