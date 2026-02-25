"""Settings window — native resize, dark title bar, auto-hiding scrollbar.
Includes: Sound picker (Windows Media), App-Trigger list, Fullscreen toggle."""

import tkinter as tk
from tkinter import filedialog
import os
import glob
import wave
import winsound

from config import Config
from autostart import is_autostart_enabled, enable_autostart, disable_autostart
import theme as T
from widgets import (
    RoundedButton, RoundedEntry, RoundedTextarea, TimeInput,
    NumberInput, CustomCheckbox, AutoHideScrollbar, fade_in_window,
    round_rect,
)


def _enable_dark_titlebar(window):
    """Enable dark title bar on Windows 10/11 via DWM API."""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        pass


# ── Helpers ──

def _section_label(parent, text):
    tk.Label(
        parent, text=text,
        font=T.FONT_LABEL, bg=T.BG, fg=T.LABEL, anchor="w",
    ).pack(anchor="w", pady=(0, 10))


def _separator(parent):
    tk.Frame(parent, bg="#222222", height=1).pack(fill="x", pady=(0, 24))


def _get_windows_sounds():
    """Scan C:\\Windows\\Media for .wav files, return sorted list."""
    media_dir = r"C:\Windows\Media"
    if not os.path.isdir(media_dir):
        return []
    wavs = glob.glob(os.path.join(media_dir, "*.wav"))
    wavs.sort(key=lambda p: os.path.basename(p).lower())
    return wavs


# ── Sound List Item ──

class _SoundRow(tk.Frame):
    """Single row in the sound picker list: name + play button, selectable."""

    # Class-level tracking: which row is currently playing
    _active_row = None

    def __init__(self, parent, filepath, display_name, is_selected, on_select,
                 on_play, on_stop, is_custom=False):
        super().__init__(parent, bg=T.BG, cursor="hand2")
        self.filepath = filepath
        self._on_select = on_select
        self._on_play = on_play
        self._on_stop = on_stop
        self._playing = False
        self._selected = is_selected

        # Selection highlight
        bg = T.BG_INPUT if is_selected else T.BG
        self.configure(bg=bg)

        # Play button — larger with rounded bg
        self._play_canvas = tk.Canvas(self, width=34, height=34,
                                       bg=bg, highlightthickness=0, bd=0,
                                       cursor="hand2")
        self._play_canvas.pack(side="left", padx=(8, 6), pady=3)
        self._play_bg = round_rect(self._play_canvas, 2, 2, 32, 32, radius=10,
                                    fill=bg, outline="")
        self._play_icon = self._play_canvas.create_text(
            17, 17, text="\u25b6", fill=T.TEXT_MUTED, font=(T.FONT, 12))
        self._play_canvas.bind("<Button-1>", self._toggle_play)
        self._play_canvas.bind("<Enter>", self._on_play_enter)
        self._play_canvas.bind("<Leave>", self._on_play_leave)

        # Name label
        self._label = tk.Label(
            self, text=display_name, font=T.FONT_BODY,
            bg=bg, fg=T.TEXT if is_selected else T.TEXT_SECONDARY,
            anchor="w",
        )
        self._label.pack(side="left", fill="x", expand=True, pady=6)

        # Custom badge
        if is_custom:
            tk.Label(self, text="Eigene", font=T.FONT_MUTED,
                     bg=bg, fg=T.TEXT_MUTED).pack(side="right", padx=(0, 10))

        # Select indicator
        if is_selected:
            tk.Label(self, text="\u2713", font=(T.FONT, 12, "bold"),
                     bg=bg, fg=T.ACCENT).pack(side="right", padx=(0, 10))

        # Click anywhere to select
        self.bind("<Button-1>", lambda e: self._on_select(filepath))
        self._label.bind("<Button-1>", lambda e: self._on_select(filepath))

        # Hover effect for whole row
        for w in (self, self._label):
            w.bind("<Enter>", self._on_enter, add="+")
            w.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, _e):
        if not self._selected:
            bg = T.BG_HOVER
            self.configure(bg=bg)
            self._label.configure(bg=bg)
            self._play_canvas.configure(bg=bg)
            if not self._playing:
                self._play_canvas.itemconfigure(self._play_bg, fill=bg)

    def _on_leave(self, _e):
        if not self._selected:
            bg = T.BG
            self.configure(bg=bg)
            self._label.configure(bg=bg)
            self._play_canvas.configure(bg=bg)
            if not self._playing:
                self._play_canvas.itemconfigure(self._play_bg, fill=bg)

    def _on_play_enter(self, _e):
        """Hover over the play button — highlight it."""
        self._play_canvas.itemconfigure(
            self._play_bg, fill=T.BG_HOVER if not self._playing else "#2a1a1a")
        self._play_canvas.itemconfigure(
            self._play_icon, fill=T.TEXT if not self._playing else T.DANGER)

    def _on_play_leave(self, _e):
        """Leave play button — reset highlight."""
        row_bg = T.BG_INPUT if self._selected else T.BG
        self._play_canvas.itemconfigure(
            self._play_bg, fill=row_bg if not self._playing else row_bg)
        self._play_canvas.itemconfigure(
            self._play_icon,
            fill=(T.ACCENT if self._playing else T.TEXT_MUTED))

    def _toggle_play(self, _e=None):
        if self._playing:
            # Stop this sound
            self._set_stopped()
            self._on_stop()
            _SoundRow._active_row = None
        else:
            # Stop any other currently playing row first
            if _SoundRow._active_row and _SoundRow._active_row is not self:
                _SoundRow._active_row._set_stopped()
            _SoundRow._active_row = self
            self._playing = True
            self._play_canvas.itemconfigure(self._play_icon,
                                             text="\u25a0", fill=T.ACCENT)
            self._on_stop()  # Stop any playing sound immediately
            self._on_play(self.filepath, self._on_play_done)

    def _set_stopped(self):
        """Reset this row to stopped state."""
        self._playing = False
        if self.winfo_exists():
            self._play_canvas.itemconfigure(self._play_icon,
                                             text="\u25b6", fill=T.TEXT_MUTED)
            row_bg = T.BG_INPUT if self._selected else T.BG
            self._play_canvas.itemconfigure(self._play_bg, fill=row_bg)

    def _on_play_done(self):
        """Called when sound finishes playing naturally."""
        if self.winfo_exists():
            self._set_stopped()
        if _SoundRow._active_row is self:
            _SoundRow._active_row = None


# ── App Trigger Row ──

class _TriggerRow(tk.Frame):
    """Single row in the trigger apps list: name + remove button."""

    def __init__(self, parent, app_name, on_remove):
        super().__init__(parent, bg=T.BG)
        self._app_name = app_name

        tk.Label(
            self, text=app_name, font=T.FONT_BODY,
            bg=T.BG, fg=T.TEXT, anchor="w",
        ).pack(side="left", padx=(10, 0), pady=6, fill="x", expand=True)

        remove_canvas = tk.Canvas(self, width=24, height=24,
                                   bg=T.BG, highlightthickness=0, bd=0, cursor="hand2")
        remove_canvas.pack(side="right", padx=(0, 10), pady=6)
        _x = remove_canvas.create_text(
            12, 12, text="\u2715", fill=T.TEXT_MUTED, font=(T.FONT, 10))
        remove_canvas.bind("<Enter>", lambda e: remove_canvas.itemconfigure(
            _x, fill=T.DANGER))
        remove_canvas.bind("<Leave>", lambda e: remove_canvas.itemconfigure(
            _x, fill=T.TEXT_MUTED))
        remove_canvas.bind("<Button-1>", lambda e: on_remove(app_name))

        # Hover
        self.bind("<Enter>", lambda e: self.configure(bg=T.BG_HOVER))
        self.bind("<Leave>", lambda e: self.configure(bg=T.BG))


# ── Collapsible Section ──

class _CollapsibleSection(tk.Frame):
    """Section with clickable header that toggles content visibility."""

    def __init__(self, parent, title, count=0, initially_open=False):
        super().__init__(parent, bg=T.BG)
        self._open = initially_open

        # Header row
        self._header = tk.Frame(self, bg=T.BG, cursor="hand2")
        self._header.pack(fill="x")

        self._arrow = tk.Label(
            self._header, text="\u25bc" if initially_open else "\u25b6",
            font=(T.FONT, 7), bg=T.BG, fg=T.TEXT_MUTED)
        self._arrow.pack(side="left", padx=(0, 8))

        self._title_label = tk.Label(
            self._header, text=title, font=T.FONT_LABEL,
            bg=T.BG, fg=T.LABEL)
        self._title_label.pack(side="left")

        self._count_label = tk.Label(
            self._header, text=f"({count})" if count else "(0)",
            font=T.FONT_MUTED, bg=T.BG, fg=T.TEXT_MUTED)
        self._count_label.pack(side="left", padx=(6, 0))

        # Content frame
        self.content = tk.Frame(self, bg=T.BG)
        if initially_open:
            self.content.pack(fill="x", pady=(10, 0))

        # Click anywhere on header to toggle
        for w in (self._header, self._arrow, self._title_label, self._count_label):
            w.bind("<Button-1>", self._toggle)

    def _toggle(self, _e=None):
        self._open = not self._open
        if self._open:
            self.content.pack(fill="x", pady=(10, 0))
            self._arrow.configure(text="\u25bc")
        else:
            self.content.pack_forget()
            self._arrow.configure(text="\u25b6")

    def update_count(self, count):
        self._count_label.configure(text=f"({count})")


# ══════════════════════════════════════════════════════════════════════
# Main Settings Window
# ══════════════════════════════════════════════════════════════════════

class SettingsWindow:
    def __init__(self, root: tk.Tk, config: Config, on_save=None, on_test=None):
        self.root = root
        self.config = config
        self.on_save = on_save
        self.on_test = on_test
        self.window = None
        self._playing_sound = False
        self._play_done_id = None

    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.root)
        self.window.attributes("-alpha", 0.0)
        self.window.title("Einstellungen")
        self.window.configure(bg=T.BG)
        self.window.attributes("-topmost", True)
        self.window.resizable(True, True)
        self.window.minsize(470, 550)
        self.window.protocol("WM_DELETE_WINDOW", self._close)

        w, h = 500, 820
        sx = self.window.winfo_screenwidth()
        sy = self.window.winfo_screenheight()
        max_w = min(800, sx - 100)
        max_h = min(1000, sy - 100)
        self.window.maxsize(max_w, max_h)
        self.window.geometry(f"{w}x{h}+{(sx-w)//2}+{(sy-h)//2}")

        self.window.update_idletasks()
        _enable_dark_titlebar(self.window)

        # ── Bottom buttons (pinned) ──
        btn_bar = tk.Frame(self.window, bg=T.BG)
        btn_bar.pack(fill="x", side="bottom", padx=28, pady=(16, 24))

        tk.Frame(btn_bar, bg="#252525", height=1).pack(fill="x", pady=(0, 16))

        btn_inner = tk.Frame(btn_bar, bg=T.BG)
        btn_inner.pack(fill="x")

        self._test_btn = RoundedButton(
            btn_inner, text="Alarm testen",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._on_test,
            width=195, height=52, radius=16,
        )
        self._test_btn.pack(side="left")

        self._save_btn = RoundedButton(
            btn_inner, text="Speichern",
            bg=T.TEXT, fg=T.BG,
            hover_bg="#e0e0e0", hover_fg=T.BG,
            command=self._on_save,
            width=195, height=52, radius=16,
        )
        self._save_btn.pack(side="right")

        # ── Scrollable content area ──
        outer = tk.Frame(self.window, bg=T.BG)
        outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(outer, bg=T.BG, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)

        self._scroll_frame = tk.Frame(self._canvas, bg=T.BG)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._scroll_frame, anchor="nw")

        self._scrollbar = AutoHideScrollbar(
            outer, command=self._canvas.yview, width=8)
        self._scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scroll_frame.bind("<Configure>", self._on_scroll_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Enter>", lambda e: self._scrollbar.show_temporarily())

        def _on_mousewheel(event):
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(_e):
            self.window.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(_e):
            try:
                self.window.unbind_all("<MouseWheel>")
            except Exception:
                pass

        outer.bind("<Enter>", _bind_wheel)
        outer.bind("<Leave>", _unbind_wheel)

        content = tk.Frame(self._scroll_frame, bg=T.BG)
        content.pack(fill="both", expand=True, padx=28, pady=(24, 28))

        # ╔═══════════════════════════════════════════╗
        # ║  1. Aktives Zeitfenster                   ║
        # ╚═══════════════════════════════════════════╝
        _section_label(content, "Aktives Zeitfenster")

        time_row = tk.Frame(content, bg=T.BG)
        time_row.pack(fill="x", pady=(0, 24))

        von_frame = tk.Frame(time_row, bg=T.BG)
        von_frame.pack(side="left")
        tk.Label(von_frame, text="Von", font=T.FONT_MUTED,
                 bg=T.BG, fg=T.TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))
        self.start_time = TimeInput(von_frame, self.config.start_hour,
                                    self.config.start_minute)
        self.start_time.pack()

        tk.Label(time_row, text="\u2192", font=(T.FONT, 18),
                 bg=T.BG, fg=T.TEXT_MUTED).pack(side="left", padx=24, pady=(18, 0))

        bis_frame = tk.Frame(time_row, bg=T.BG)
        bis_frame.pack(side="left")
        tk.Label(bis_frame, text="Bis", font=T.FONT_MUTED,
                 bg=T.BG, fg=T.TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))
        self.end_time = TimeInput(bis_frame, self.config.end_hour,
                                  self.config.end_minute)
        self.end_time.pack()

        _separator(content)

        # ╔═══════════════════════════════════════════╗
        # ║  2. Schlummer-Intervall                   ║
        # ╚═══════════════════════════════════════════╝
        _section_label(content, "Schlummer-Intervall")
        self.snooze_input = NumberInput(content, value=self.config.snooze_minutes,
                                        min_val=1, max_val=999, suffix="Minuten")
        self.snooze_input.pack(anchor="w", pady=(0, 24))

        _separator(content)

        # ╔═══════════════════════════════════════════╗
        # ║  3. Alarm-Sound (Dropdown-Picker)          ║
        # ╚═══════════════════════════════════════════╝
        _section_label(content, "Alarm-Sound")

        # Gather all sounds
        self._windows_sounds = _get_windows_sounds()
        self._custom_sounds = list(self.config.custom_sounds)
        self._selected_sound = self.config.sound_file
        self._sound_popup = None

        # If no sound selected, pick first alarm sound
        if not self._selected_sound and self._windows_sounds:
            alarm_sounds = [s for s in self._windows_sounds if "alarm" in os.path.basename(s).lower()]
            self._selected_sound = alarm_sounds[0] if alarm_sounds else self._windows_sounds[0]

        # Sound row: [▶ play] [dropdown ▼] [+ add]
        sound_row = tk.Frame(content, bg=T.BG)
        sound_row.pack(fill="x", pady=(0, 24))

        self._sound_play_btn = RoundedButton(
            sound_row, text="\u25b6",
            bg=T.BG_INPUT, fg=T.TEXT_MUTED,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._play_current_sound,
            width=42, height=42, radius=12, font=(T.FONT, 11),
        )
        self._sound_play_btn.pack(side="left", padx=(0, 8))

        self._sound_dropdown = tk.Canvas(
            sound_row, height=42,
            bg=T.BG, highlightthickness=0, bd=0, cursor="hand2",
        )
        self._sound_dropdown.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._sound_dropdown.bind("<Configure>", self._draw_sound_dropdown)
        self._sound_dropdown.bind("<Button-1>", lambda e: self._toggle_sound_popup())
        self._sound_dd_hovering = False
        self._sound_dropdown.bind("<Enter>", self._on_sound_dd_enter)
        self._sound_dropdown.bind("<Leave>", self._on_sound_dd_leave)

        add_sound_btn = RoundedButton(
            sound_row, text="+",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._add_custom_sound,
            width=42, height=42, radius=12, font=(T.FONT, 14),
        )
        add_sound_btn.pack(side="right")

        _separator(content)

        # ╔═══════════════════════════════════════════╗
        # ║  4. Popup-Text                            ║
        # ╚═══════════════════════════════════════════╝
        _section_label(content, "Popup-Text")
        tk.Label(content, text="Wird im Alarm-Popup als Untertitel angezeigt",
                 font=T.FONT_MUTED, bg=T.BG, fg=T.TEXT_MUTED).pack(
            anchor="w", pady=(0, 8))

        self.popup_textarea = RoundedTextarea(content, width=410, height=80, radius=12)
        self.popup_textarea.pack(anchor="w", pady=(0, 24))
        self.popup_textarea.set_text(self.config.popup_text)

        _separator(content)

        # ╔═══════════════════════════════════════════╗
        # ║  5. Fullscreen-Popup                      ║
        # ╚═══════════════════════════════════════════╝
        _section_label(content, "Alarm-Anzeige")
        self.fullscreen_var = tk.BooleanVar(value=self.config.fullscreen_popup)
        CustomCheckbox(content, "Fullscreen-Alarm (ganzer Bildschirm, kein Wegklicken)",
                       self.fullscreen_var).pack(anchor="w", pady=(0, 24))

        _separator(content)

        # ╔═══════════════════════════════════════════╗
        # ║  6. Website-Trigger (collapsible)           ║
        # ╚═══════════════════════════════════════════╝
        self._trigger_sites = list(self.config.trigger_sites)
        self._sites_section = _CollapsibleSection(
            content, "Website-Trigger", count=len(self._trigger_sites))
        self._sites_section.pack(fill="x", pady=(0, 8))
        sc = self._sites_section.content

        tk.Label(sc,
                 text="Nach Bestätigung der Abendroutine: Alarm kommt zurück\n"
                      "wenn du eine dieser Seiten in Chrome/Edge besuchst",
                 font=T.FONT_MUTED, bg=T.BG, fg=T.TEXT_MUTED,
                 justify="left").pack(anchor="w", pady=(0, 8))

        self._sites_list_frame = tk.Frame(sc, bg=T.BORDER)
        self._sites_list_frame.pack(fill="x", pady=(0, 8))
        self._sites_inner = tk.Frame(self._sites_list_frame, bg=T.BG)
        self._sites_inner.pack(fill="x", padx=1, pady=1)
        self._rebuild_sites_list()

        add_site_row = tk.Frame(sc, bg=T.BG)
        add_site_row.pack(fill="x")

        self._site_entry = RoundedEntry(
            add_site_row, width=280, height=40, radius=12, font=T.FONT_BODY)
        self._site_entry.pack(side="left")
        self._site_entry.entry.insert(0, "website.com")
        self._site_entry.entry.bind("<FocusIn>", self._site_entry_focus_in)
        self._site_entry.entry.bind("<Return>", lambda e: self._add_site())

        RoundedButton(
            add_site_row, text="+ Hinzufügen",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._add_site,
            width=140, height=40, radius=12, font=T.FONT_BUTTON,
        ).pack(side="left", padx=(10, 0))

        _separator(content)

        # ╔═══════════════════════════════════════════╗
        # ║  7. App-Trigger (collapsible)              ║
        # ╚═══════════════════════════════════════════╝
        self._trigger_apps = list(self.config.trigger_apps)
        self._apps_section = _CollapsibleSection(
            content, "App-Trigger", count=len(self._trigger_apps))
        self._apps_section.pack(fill="x", pady=(0, 8))
        ac = self._apps_section.content

        tk.Label(ac,
                 text="Alarm wird auch ausgelöst wenn eine dieser Apps\n"
                      "geöffnet wird (z.B. Spiele)",
                 font=T.FONT_MUTED, bg=T.BG, fg=T.TEXT_MUTED,
                 justify="left").pack(anchor="w", pady=(0, 8))

        self._trigger_list_frame = tk.Frame(ac, bg=T.BORDER)
        self._trigger_list_frame.pack(fill="x", pady=(0, 8))
        self._trigger_inner = tk.Frame(self._trigger_list_frame, bg=T.BG)
        self._trigger_inner.pack(fill="x", padx=1, pady=1)
        self._rebuild_trigger_list()

        add_trigger_row = tk.Frame(ac, bg=T.BG)
        add_trigger_row.pack(fill="x")

        self._trigger_entry = RoundedEntry(
            add_trigger_row, width=250, height=40, radius=12, font=T.FONT_BODY)
        self._trigger_entry.pack(side="left")
        self._trigger_entry.entry.insert(0, "prozess.exe")
        self._trigger_entry.entry.bind("<FocusIn>", self._trigger_entry_focus_in)
        self._trigger_entry.entry.bind("<Return>", lambda e: self._add_trigger())

        RoundedButton(
            add_trigger_row, text="+ Hinzufügen",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._add_trigger,
            width=140, height=40, radius=12, font=T.FONT_BUTTON,
        ).pack(side="left", padx=(10, 0))

        RoundedButton(
            add_trigger_row, text="\u2026",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._browse_trigger,
            width=40, height=40, radius=12, font=T.FONT_BUTTON,
        ).pack(side="left", padx=(6, 0))

        _separator(content)

        # ╔═══════════════════════════════════════════╗
        # ║  8. Auto-Start Apps (collapsible)          ║
        # ╚═══════════════════════════════════════════╝
        self._launch_apps = list(self.config.launch_apps)
        self._launch_section = _CollapsibleSection(
            content, "Auto-Start Apps", count=len(self._launch_apps))
        self._launch_section.pack(fill="x", pady=(0, 8))
        lc = self._launch_section.content

        tk.Label(lc,
                 text="Diese Apps werden automatisch gestartet wenn du\n"
                      "die Abendroutine bestätigst",
                 font=T.FONT_MUTED, bg=T.BG, fg=T.TEXT_MUTED,
                 justify="left").pack(anchor="w", pady=(0, 8))

        self._launch_list_frame = tk.Frame(lc, bg=T.BORDER)
        self._launch_list_frame.pack(fill="x", pady=(0, 8))
        self._launch_inner = tk.Frame(self._launch_list_frame, bg=T.BG)
        self._launch_inner.pack(fill="x", padx=1, pady=1)
        self._rebuild_launch_list()

        add_launch_row = tk.Frame(lc, bg=T.BG)
        add_launch_row.pack(fill="x")

        self._launch_entry = RoundedEntry(
            add_launch_row, width=250, height=40, radius=12, font=T.FONT_BODY)
        self._launch_entry.pack(side="left")
        self._launch_entry.entry.insert(0, "app.exe")
        self._launch_entry.entry.bind("<FocusIn>", self._launch_entry_focus_in)
        self._launch_entry.entry.bind("<Return>", lambda e: self._add_launch_app())

        RoundedButton(
            add_launch_row, text="+ Hinzufügen",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._add_launch_app,
            width=140, height=40, radius=12, font=T.FONT_BUTTON,
        ).pack(side="left", padx=(10, 0))

        RoundedButton(
            add_launch_row, text="\u2026",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._browse_launch_app,
            width=40, height=40, radius=12, font=T.FONT_BUTTON,
        ).pack(side="left", padx=(6, 0))

        _separator(content)

        # ╔═══════════════════════════════════════════╗
        # ║  9. Autostart                             ║
        # ╚═══════════════════════════════════════════╝
        self.autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        CustomCheckbox(content, "Mit Windows starten", self.autostart_var).pack(
            anchor="w", pady=(0, 8))

        # Fade-in
        fade_in_window(self.window, duration_ms=250)

    # ── Scroll / Canvas ──

    def _on_scroll_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

    # ══════════════════════════════════════════════════
    # Sound Picker (Dropdown)
    # ══════════════════════════════════════════════════

    def _get_sound_display_name(self):
        if not self._selected_sound:
            return "Kein Sound"
        return os.path.splitext(os.path.basename(self._selected_sound))[0]

    def _draw_sound_dropdown(self, _event=None):
        c = self._sound_dropdown
        c.delete("all")
        w = c.winfo_width()
        h = 42
        bg = T.BG_HOVER if self._sound_dd_hovering else T.BG_INPUT
        round_rect(c, 0, 0, w, h, radius=12, fill=bg, outline=T.BORDER)
        name = self._get_sound_display_name()
        c.create_text(16, h // 2, text=name, fill=T.TEXT,
                      font=T.FONT_BODY, anchor="w")
        c.create_text(w - 16, h // 2, text="\u25bc", fill=T.TEXT_MUTED,
                      font=(T.FONT, 8), anchor="e")

    def _on_sound_dd_enter(self, _e):
        self._sound_dd_hovering = True
        self._draw_sound_dropdown()

    def _on_sound_dd_leave(self, _e):
        self._sound_dd_hovering = False
        self._draw_sound_dropdown()

    def _toggle_sound_popup(self):
        if self._sound_popup and self._sound_popup.winfo_exists():
            self._close_sound_popup()
        else:
            self._show_sound_popup()

    def _show_sound_popup(self):
        self._close_sound_popup()

        popup = tk.Toplevel(self.window)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=T.BORDER)
        self._sound_popup = popup

        # Position below dropdown
        self._sound_dropdown.update_idletasks()
        x = self._sound_dropdown.winfo_rootx()
        y = (self._sound_dropdown.winfo_rooty()
             + self._sound_dropdown.winfo_height() + 4)
        w = self._sound_dropdown.winfo_width()

        row_h = 40
        max_visible = 8
        total_sounds = len(self._windows_sounds) + len(self._custom_sounds)
        if self._custom_sounds:
            total_sounds += 1  # separator row
        visible_rows = min(max(total_sounds, 1), max_visible)
        popup_h = visible_rows * row_h + 2

        popup.geometry(f"{w}x{popup_h}+{x}+{y}")

        # Inner content
        inner = tk.Frame(popup, bg=T.BG)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        sp_canvas = tk.Canvas(inner, bg=T.BG, highlightthickness=0, bd=0)
        sp_canvas.pack(fill="both", expand=True, side="left")
        self._sp_canvas = sp_canvas

        scroll_frame = tk.Frame(sp_canvas, bg=T.BG)
        sp_win = sp_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        if total_sounds > max_visible:
            sp_scrollbar = AutoHideScrollbar(
                inner, command=sp_canvas.yview, width=6)
            sp_scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
            sp_canvas.configure(yscrollcommand=sp_scrollbar.set)
            sp_scrollbar.show_temporarily()

        scroll_frame.bind(
            "<Configure>",
            lambda e: sp_canvas.configure(scrollregion=sp_canvas.bbox("all")))
        sp_canvas.bind(
            "<Configure>",
            lambda e: sp_canvas.itemconfigure(sp_win, width=e.width))

        # Mousewheel scrolling inside popup
        def _on_mousewheel(event):
            sp_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        for w_bind in (popup, sp_canvas, scroll_frame):
            w_bind.bind("<MouseWheel>", _on_mousewheel)

        # Build sound rows — alarm-related first
        alarm_first = sorted(
            self._windows_sounds,
            key=lambda p: (
                0 if "alarm" in os.path.basename(p).lower() else 1,
                os.path.basename(p).lower()))

        for filepath in alarm_first:
            name = os.path.splitext(os.path.basename(filepath))[0]
            selected = (filepath == self._selected_sound)
            row = _SoundRow(
                scroll_frame, filepath, name, selected,
                on_select=self._select_sound,
                on_play=self._play_preview,
                on_stop=self._stop_preview,
            )
            row.pack(fill="x")
            row.bind("<MouseWheel>", _on_mousewheel)
            for child in row.winfo_children():
                child.bind("<MouseWheel>", _on_mousewheel)

        # Custom sounds
        if self._custom_sounds:
            sep = tk.Frame(scroll_frame, bg=T.BORDER, height=1)
            sep.pack(fill="x", padx=10, pady=4)
            lbl = tk.Label(scroll_frame, text="Eigene Sounds",
                           font=T.FONT_MUTED, bg=T.BG, fg=T.TEXT_MUTED)
            lbl.pack(anchor="w", padx=10, pady=(2, 4))
            lbl.bind("<MouseWheel>", _on_mousewheel)

            for filepath in self._custom_sounds:
                if not os.path.isfile(filepath):
                    continue
                name = os.path.splitext(os.path.basename(filepath))[0]
                selected = (filepath == self._selected_sound)
                row = _SoundRow(
                    scroll_frame, filepath, name, selected,
                    on_select=self._select_sound,
                    on_play=self._play_preview,
                    on_stop=self._stop_preview,
                    is_custom=True,
                )
                row.pack(fill="x")
                row.bind("<MouseWheel>", _on_mousewheel)
                for child in row.winfo_children():
                    child.bind("<MouseWheel>", _on_mousewheel)

        # Scroll to currently selected sound
        popup.update_idletasks()
        self._scroll_to_selected(scroll_frame, sp_canvas)

        # Close on deactivate (click outside) or Escape
        popup.bind("<Deactivate>",
                   lambda e: self.window.after(100, self._close_sound_popup))
        popup.bind("<Escape>", lambda e: self._close_sound_popup())
        popup.focus_set()

    def _scroll_to_selected(self, scroll_frame, canvas):
        """Scroll the sound popup so the selected item is visible."""
        for child in scroll_frame.winfo_children():
            if isinstance(child, _SoundRow) and child._selected:
                canvas.update_idletasks()
                child_y = child.winfo_y()
                canvas_h = canvas.winfo_height()
                scroll_h = scroll_frame.winfo_reqheight()
                if scroll_h > canvas_h:
                    fraction = max(0.0, (child_y - canvas_h // 2) / scroll_h)
                    canvas.yview_moveto(fraction)
                break

    def _close_sound_popup(self):
        if self._sound_popup and self._sound_popup.winfo_exists():
            self._sound_popup.destroy()
        self._sound_popup = None

    def _select_sound(self, filepath):
        self._selected_sound = filepath
        self._close_sound_popup()
        self._draw_sound_dropdown()

    def _play_current_sound(self):
        """Play/stop the currently selected sound."""
        if self._playing_sound:
            self._stop_preview()
            self._sound_play_btn.itemconfigure(
                self._sound_play_btn._label, text="\u25b6")
        elif self._selected_sound and os.path.isfile(self._selected_sound):
            self._sound_play_btn.itemconfigure(
                self._sound_play_btn._label, text="\u25a0")
            self._play_preview(
                self._selected_sound, self._on_current_play_done)

    def _on_current_play_done(self):
        if (hasattr(self, '_sound_play_btn')
                and self.window and self.window.winfo_exists()):
            self._sound_play_btn.itemconfigure(
                self._sound_play_btn._label, text="\u25b6")

    def _play_preview(self, filepath, on_done_callback):
        """Play a sound file asynchronously — can be stopped instantly."""
        self._stop_preview()
        self._playing_sound = True

        try:
            winsound.PlaySound(
                filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            self._playing_sound = False
            return

        # Auto-reset button when sound finishes
        duration_ms = self._get_wav_duration_ms(filepath)
        if duration_ms and self.window and self.window.winfo_exists():
            self._play_done_id = self.window.after(
                duration_ms, self._on_play_finished, on_done_callback)

    def _get_wav_duration_ms(self, filepath):
        """Get duration of a WAV file in milliseconds."""
        try:
            with wave.open(filepath, 'r') as w:
                return int((w.getnframes() / w.getframerate()) * 1000)
        except Exception:
            return 3000  # fallback 3s

    def _on_play_finished(self, callback):
        """Called when async sound finishes naturally."""
        self._playing_sound = False
        if callback:
            callback()

    def _stop_preview(self):
        """Stop any currently playing preview sound immediately."""
        # Cancel auto-reset timer
        if hasattr(self, '_play_done_id') and self._play_done_id:
            try:
                self.window.after_cancel(self._play_done_id)
            except Exception:
                pass
            self._play_done_id = None

        if self._playing_sound:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
            self._playing_sound = False

    def _add_custom_sound(self):
        self._close_sound_popup()
        self.window.attributes("-topmost", False)
        path = filedialog.askopenfilename(
            title="Eigenen Sound hinzufügen",
            initialdir=r"C:\Windows\Media",
            filetypes=[("WAV Dateien", "*.wav"), ("Alle Dateien", "*.*")]
        )
        self.window.attributes("-topmost", True)
        if path and path not in self._custom_sounds and path not in self._windows_sounds:
            self._custom_sounds.append(path)
            self._selected_sound = path
            self._draw_sound_dropdown()

    # ══════════════════════════════════════════════════
    # Website-Trigger
    # ══════════════════════════════════════════════════

    def _rebuild_sites_list(self):
        """Rebuild the trigger sites list UI."""
        for w in self._sites_inner.winfo_children():
            w.destroy()

        if hasattr(self, '_sites_section'):
            self._sites_section.update_count(len(self._trigger_sites))

        if not self._trigger_sites:
            tk.Label(self._sites_inner,
                     text="Keine Websites konfiguriert",
                     font=T.FONT_MUTED, bg=T.BG, fg=T.TEXT_MUTED,
                     ).pack(padx=10, pady=12)
            return

        for site_name in self._trigger_sites:
            row = _TriggerRow(self._sites_inner, site_name,
                              on_remove=self._remove_site)
            row.pack(fill="x")

    def _add_site(self):
        name = self._site_entry.get().strip().lower()
        if not name or name == "website.com":
            return
        # Clean up — remove protocol/path if user pasted a full URL
        name = name.replace("https://", "").replace("http://", "")
        name = name.replace("www.", "")
        name = name.split("/")[0]  # just the domain
        if name not in [s.lower() for s in self._trigger_sites]:
            self._trigger_sites.append(name)
            self._rebuild_sites_list()
        self._site_entry.entry.delete(0, "end")

    def _remove_site(self, site_name):
        self._trigger_sites = [s for s in self._trigger_sites if s != site_name]
        self._rebuild_sites_list()

    def _site_entry_focus_in(self, _e):
        if self._site_entry.get() == "website.com":
            self._site_entry.entry.delete(0, "end")

    # ══════════════════════════════════════════════════
    # App-Trigger
    # ══════════════════════════════════════════════════

    def _rebuild_trigger_list(self):
        """Rebuild the trigger apps list UI."""
        for w in self._trigger_inner.winfo_children():
            w.destroy()

        if hasattr(self, '_apps_section'):
            self._apps_section.update_count(len(self._trigger_apps))

        if not self._trigger_apps:
            tk.Label(self._trigger_inner,
                     text="Keine Apps konfiguriert",
                     font=T.FONT_MUTED, bg=T.BG, fg=T.TEXT_MUTED,
                     ).pack(padx=10, pady=12)
            return

        for app_name in self._trigger_apps:
            row = _TriggerRow(self._trigger_inner, app_name,
                              on_remove=self._remove_trigger)
            row.pack(fill="x")

    def _add_trigger(self):
        name = self._trigger_entry.get().strip()
        if not name or name == "prozess.exe":
            return
        # Ensure .exe suffix
        if not name.lower().endswith(".exe"):
            name += ".exe"
        if name.lower() not in [a.lower() for a in self._trigger_apps]:
            self._trigger_apps.append(name)
            self._rebuild_trigger_list()
        self._trigger_entry.entry.delete(0, "end")

    def _remove_trigger(self, app_name):
        self._trigger_apps = [a for a in self._trigger_apps if a != app_name]
        self._rebuild_trigger_list()

    def _trigger_entry_focus_in(self, _e):
        if self._trigger_entry.get() == "prozess.exe":
            self._trigger_entry.entry.delete(0, "end")

    def _browse_trigger(self):
        self.window.attributes("-topmost", False)
        path = filedialog.askopenfilename(
            title="App auswählen",
            filetypes=[("Programme", "*.exe"), ("Alle Dateien", "*.*")]
        )
        self.window.attributes("-topmost", True)
        if path:
            name = os.path.basename(path)
            if name.lower() not in [a.lower() for a in self._trigger_apps]:
                self._trigger_apps.append(name)
                self._rebuild_trigger_list()

    # ══════════════════════════════════════════════════
    # Auto-Start Apps
    # ══════════════════════════════════════════════════

    def _rebuild_launch_list(self):
        """Rebuild the launch apps list UI."""
        for w in self._launch_inner.winfo_children():
            w.destroy()

        if hasattr(self, '_launch_section'):
            self._launch_section.update_count(len(self._launch_apps))

        if not self._launch_apps:
            tk.Label(self._launch_inner,
                     text="Keine Apps konfiguriert",
                     font=T.FONT_MUTED, bg=T.BG, fg=T.TEXT_MUTED,
                     ).pack(padx=10, pady=12)
            return

        for app_path in self._launch_apps:
            display = os.path.basename(app_path)
            row = _TriggerRow(self._launch_inner, display,
                              on_remove=lambda name, p=app_path: self._remove_launch_app(p))
            row.pack(fill="x")

    def _add_launch_app(self):
        name = self._launch_entry.get().strip()
        if not name or name == "app.exe":
            return
        if name not in self._launch_apps:
            self._launch_apps.append(name)
            self._rebuild_launch_list()
        self._launch_entry.entry.delete(0, "end")

    def _launch_entry_focus_in(self, _e):
        if self._launch_entry.get() == "app.exe":
            self._launch_entry.entry.delete(0, "end")

    def _browse_launch_app(self):
        self.window.attributes("-topmost", False)
        path = filedialog.askopenfilename(
            title="App auswählen",
            filetypes=[("Programme & Verknüpfungen", "*.exe;*.lnk"),
                       ("Alle Dateien", "*.*")]
        )
        self.window.attributes("-topmost", True)
        if path and path not in self._launch_apps:
            self._launch_apps.append(path)
            self._rebuild_launch_list()

    def _remove_launch_app(self, app_path):
        self._launch_apps = [p for p in self._launch_apps if p != app_path]
        self._rebuild_launch_list()

    # ══════════════════════════════════════════════════
    # Save / Close
    # ══════════════════════════════════════════════════

    def _on_save(self):
        self._stop_preview()

        self.config.start_hour = self.start_time.hour
        self.config.start_minute = self.start_time.minute
        self.config.end_hour = self.end_time.hour
        self.config.end_minute = self.end_time.minute
        self.config.snooze_minutes = self.snooze_input.get()
        self.config.popup_text = self.popup_textarea.get_text()
        self.config.fullscreen_popup = self.fullscreen_var.get()
        self.config.trigger_sites = list(self._trigger_sites)
        self.config.trigger_apps = list(self._trigger_apps)
        self.config.launch_apps = list(self._launch_apps)
        self.config.custom_sounds = list(self._custom_sounds)
        self.config.sound_file = self._selected_sound or ""

        if self.autostart_var.get():
            enable_autostart()
        else:
            disable_autostart()
        self.config.autostart = self.autostart_var.get()

        self.config.save()
        if self.on_save:
            self.on_save()

        # Success flash then close
        self._save_btn.itemconfigure(self._save_btn._rect, fill=T.SUCCESS)
        self._save_btn.itemconfigure(self._save_btn._label, text="\u2713", fill=T.BG)
        self.window.after(400, self._close)

    def _close(self):
        self._stop_preview()
        self._close_sound_popup()
        try:
            self.window.unbind_all("<MouseWheel>")
        except Exception:
            pass
        if self.window and self.window.winfo_exists():
            self.window.destroy()

    def _on_test(self):
        if self.on_test:
            self.on_test()
