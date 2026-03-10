"""Settings window — native resize, dark title bar, auto-hiding scrollbar.
Includes: Schedule profiles with inline triggers, sound picker, fullscreen toggle."""

import tkinter as tk
from tkinter import filedialog
import os
import glob
import wave
import winsound

from config import Config, ScheduleProfile, TriggerEntry, TriggerSchedule
from autostart import is_autostart_enabled, enable_autostart, disable_autostart
import theme as T
from widgets import (
    RoundedButton, RoundedEntry, RoundedTextarea, TimeInput,
    NumberInput, CustomCheckbox, AutoHideScrollbar, CollapsibleSection,
    EmojiPicker, fade_in_window, round_rect,
    draw_close_x, draw_play, draw_stop,
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


# -- Helpers --

def _section_label(parent, text):
    row = tk.Frame(parent, bg=T.BG)
    row.pack(anchor="w", fill="x", pady=(0, 10))
    dot = tk.Canvas(row, width=8, height=8, bg=T.BG, highlightthickness=0, bd=0)
    dot.pack(side="left", padx=(0, 10), pady=4)
    dot.create_oval(1, 1, 7, 7, fill=T.ACCENT, outline="")
    tk.Label(row, text=text, font=T.FONT_SECTION, bg=T.BG, fg=T.TEXT, anchor="w").pack(side="left")


def _separator(parent):
    tk.Frame(parent, bg=T.SEPARATOR_COLOR, height=1).pack(fill="x", pady=(0, 24))


def _get_windows_sounds():
    """Scan C:\\Windows\\Media for .wav files, return sorted list."""
    media_dir = r"C:\Windows\Media"
    if not os.path.isdir(media_dir):
        return []
    wavs = glob.glob(os.path.join(media_dir, "*.wav"))
    wavs.sort(key=lambda p: os.path.basename(p).lower())
    return wavs


# -- Sound List Item --

class _SoundRow(tk.Frame):
    """Single row in the sound picker list: name + play button, selectable."""

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

        bg = T.BG_INPUT if is_selected else T.BG
        self.configure(bg=bg)

        self._play_canvas = tk.Canvas(self, width=34, height=34,
                                       bg=bg, highlightthickness=0, bd=0,
                                       cursor="hand2")
        self._play_canvas.pack(side="left", padx=(8, 6), pady=3)
        self._play_bg = round_rect(self._play_canvas, 2, 2, 32, 32, radius=12,
                                    fill=bg, outline="")
        self._play_icon_items = draw_play(self._play_canvas, 17, 17, 10, T.TEXT_MUTED)
        self._play_mode = "play"
        self._play_canvas.bind("<Button-1>", self._toggle_play)
        self._play_canvas.bind("<Enter>", self._on_play_enter)
        self._play_canvas.bind("<Leave>", self._on_play_leave)

        self._label = tk.Label(
            self, text=display_name, font=T.FONT_BODY,
            bg=bg, fg=T.TEXT if is_selected else T.TEXT_SECONDARY,
            anchor="w",
        )
        self._label.pack(side="left", fill="x", expand=True, pady=6)

        if is_custom:
            tk.Label(self, text="Eigene", font=T.FONT_MUTED,
                     bg=bg, fg=T.TEXT_MUTED).pack(side="right", padx=(0, 10))

        if is_selected:
            tk.Label(self, text="\u2713", font=(T.FONT, 12, "bold"),
                     bg=bg, fg=T.ACCENT).pack(side="right", padx=(0, 10))

        self.bind("<Button-1>", lambda e: self._on_select(filepath))
        self._label.bind("<Button-1>", lambda e: self._on_select(filepath))

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
        self._play_canvas.itemconfigure(
            self._play_bg, fill=T.BG_HOVER if not self._playing else "#2a1a1a")
        color = T.TEXT if not self._playing else T.DANGER
        for item in self._play_icon_items:
            self._play_canvas.itemconfigure(item, fill=color)

    def _on_play_leave(self, _e):
        row_bg = T.BG_INPUT if self._selected else T.BG
        self._play_canvas.itemconfigure(self._play_bg, fill=row_bg)
        color = T.ACCENT if self._playing else T.TEXT_MUTED
        for item in self._play_icon_items:
            self._play_canvas.itemconfigure(item, fill=color)

    def _toggle_play(self, _e=None):
        if self._playing:
            self._set_stopped()
            self._on_stop()
            _SoundRow._active_row = None
        else:
            if _SoundRow._active_row and _SoundRow._active_row is not self:
                _SoundRow._active_row._set_stopped()
            _SoundRow._active_row = self
            self._playing = True
            self._redraw_icon("stop", T.ACCENT)
            self._on_stop()
            self._on_play(self.filepath, self._on_play_done)

    def _redraw_icon(self, mode, color):
        for item in self._play_icon_items:
            self._play_canvas.delete(item)
        if mode == "stop":
            self._play_icon_items = draw_stop(self._play_canvas, 17, 17, 10, color)
        else:
            self._play_icon_items = draw_play(self._play_canvas, 17, 17, 10, color)
        self._play_mode = mode

    def _set_stopped(self):
        self._playing = False
        if self.winfo_exists():
            self._redraw_icon("play", T.TEXT_MUTED)
            row_bg = T.BG_INPUT if self._selected else T.BG
            self._play_canvas.itemconfigure(self._play_bg, fill=row_bg)

    def _on_play_done(self):
        if self.winfo_exists():
            self._set_stopped()
        if _SoundRow._active_row is self:
            _SoundRow._active_row = None


# -- Trigger Row --

class _TriggerRow(tk.Frame):
    """Single row in a trigger/app list: name + remove button."""

    def __init__(self, parent, display_name, on_remove, badge=None, bg=None):
        row_bg = bg or T.BG
        super().__init__(parent, bg=row_bg)
        self._name = display_name

        tk.Label(
            self, text=display_name, font=T.FONT_BODY,
            bg=row_bg, fg=T.TEXT, anchor="w",
        ).pack(side="left", padx=(10, 0), pady=6, fill="x", expand=True)

        if badge:
            tk.Label(self, text=badge, font=T.FONT_MUTED,
                     bg=row_bg, fg=T.TEXT_MUTED).pack(side="right", padx=(0, 6))

        remove_canvas = tk.Canvas(self, width=24, height=24,
                                   bg=row_bg, highlightthickness=0, bd=0, cursor="hand2")
        remove_canvas.pack(side="right", padx=(0, 10), pady=6)
        _x_items = draw_close_x(remove_canvas, 12, 12, 8, T.TEXT_MUTED)
        remove_canvas.bind("<Enter>", lambda e: [remove_canvas.itemconfigure(
            i, fill=T.DANGER) for i in _x_items])
        remove_canvas.bind("<Leave>", lambda e: [remove_canvas.itemconfigure(
            i, fill=T.TEXT_MUTED) for i in _x_items])
        remove_canvas.bind("<Button-1>", lambda e: on_remove(display_name))

        self.bind("<Enter>", lambda e: self.configure(bg=T.BG_HOVER))
        self.bind("<Leave>", lambda e: self.configure(bg=row_bg))


# -- Profile Card --

class _ProfileCard(tk.Frame):
    """Editable card for a single ScheduleProfile. Self-contained with triggers."""

    def __init__(self, parent, profile, triggers, config, on_delete=None, deletable=True):
        super().__init__(parent, bg=T.BORDER, highlightthickness=0)
        self.profile = profile
        self.config = config
        self._site_triggers = [t.name for t in triggers if t.type == "site"]
        self._app_triggers = [t.name for t in triggers if t.type == "app"]

        # Gold accent line at top + border wrapper
        tk.Frame(self, bg=T.ACCENT_MUTED, height=3).pack(fill="x")
        self._card_body = tk.Frame(self, bg=T.BG_CARD)
        self._card_body.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        inner = tk.Frame(self._card_body, bg=T.BG_CARD)
        inner.pack(fill="x", padx=T.CARD_PADDING + 4, pady=(T.CARD_PADDING + 2, T.CARD_PADDING + 4))

        # -- Collapsible header: profile name + time display + delete --
        header = tk.Frame(inner, bg=T.BG_CARD, cursor="hand2")
        header.pack(fill="x")

        self._arrow = tk.Label(
            header, text="\u25b8", font=(T.FONT, 16),
            bg=T.BG_CARD, fg=T.TEXT_MUTED)
        self._arrow.pack(side="left", padx=(0, 8))

        self._header_title = tk.Label(
            header, text=f"{profile.name}  ({profile.schedule.display})",
            font=T.FONT_SECTION, bg=T.BG_CARD, fg=T.TEXT)
        self._header_title.pack(side="left")

        if deletable and on_delete:
            del_canvas = tk.Canvas(header, width=24, height=24,
                                    bg=T.BG_CARD, highlightthickness=0, bd=0,
                                    cursor="hand2")
            del_canvas.pack(side="right")
            _x_items = draw_close_x(del_canvas, 12, 12, 8, T.TEXT_MUTED)
            del_canvas.bind("<Enter>", lambda e: [del_canvas.itemconfigure(
                i, fill=T.DANGER) for i in _x_items])
            del_canvas.bind("<Leave>", lambda e: [del_canvas.itemconfigure(
                i, fill=T.TEXT_MUTED) for i in _x_items])
            del_canvas.bind("<Button-1>", lambda e: on_delete(profile.id))

        # -- Collapsible content --
        self._content = tk.Frame(inner, bg=T.BG_CARD)
        # Start collapsed
        self._is_open = False

        for w in (header, self._arrow, self._header_title):
            w.bind("<Button-1>", self._toggle_card)

        # Hover feedback
        self._header_widgets = [header, self._arrow, self._header_title]
        for w in self._header_widgets:
            w.bind("<Enter>", self._on_header_enter, add="+")
            w.bind("<Leave>", self._on_header_leave, add="+")

        self._build_content()

    def _toggle_card(self, _e=None):
        self._is_open = not self._is_open
        if self._is_open:
            self._content.pack(fill="x", pady=(T.SPACE_MD, 0))
            self._arrow.configure(text="\u25be")
        else:
            self._content.pack_forget()
            self._arrow.configure(text="\u25b8")

    def _on_header_enter(self, _e=None):
        hover = getattr(T, 'BG_CARD_HOVER', '#1c1c1c')
        for w in self._header_widgets:
            w.configure(bg=hover)

    def _on_header_leave(self, _e=None):
        for w in self._header_widgets:
            w.configure(bg=T.BG_CARD)

    def _setup_placeholder(self, entry_widget, placeholder_text):
        """Add grey placeholder text that disappears on focus."""
        entry = entry_widget.entry
        if not entry.get():
            entry.insert(0, placeholder_text)
            entry.configure(fg=T.TEXT_MUTED)

        def _on_focus_in(_e):
            if entry.get() == placeholder_text and entry.cget("fg") == T.TEXT_MUTED:
                entry.delete(0, "end")
                entry.configure(fg=T.TEXT)

        def _on_focus_out(_e):
            if not entry.get():
                entry.insert(0, placeholder_text)
                entry.configure(fg=T.TEXT_MUTED)

        entry.bind("<FocusIn>", _on_focus_in, add="+")
        entry.bind("<FocusOut>", _on_focus_out, add="+")
        entry_widget._placeholder = placeholder_text

    def _setup_textarea_placeholder(self, textarea_widget, placeholder_text):
        """Add grey placeholder text for textarea."""
        text = textarea_widget.text
        if not textarea_widget.get_text():
            text.insert("1.0", placeholder_text)
            text.configure(fg=T.TEXT_MUTED)

        def _on_focus_in(_e):
            if textarea_widget.get_text() == placeholder_text and text.cget("fg") == T.TEXT_MUTED:
                text.delete("1.0", "end")
                text.configure(fg=T.TEXT)

        def _on_focus_out(_e):
            if not textarea_widget.get_text().strip():
                text.delete("1.0", "end")
                text.insert("1.0", placeholder_text)
                text.configure(fg=T.TEXT_MUTED)

        text.bind("<FocusIn>", _on_focus_in, add="+")
        text.bind("<FocusOut>", _on_focus_out, add="+")
        textarea_widget._placeholder = placeholder_text

    def _build_content(self):
        c = self._content
        card_bg = T.BG_CARD

        # Name
        name_row = tk.Frame(c, bg=card_bg)
        name_row.pack(fill="x", pady=(0, T.SPACE_MD))
        tk.Label(name_row, text="Name", font=T.FONT_MUTED,
                 bg=card_bg, fg=T.TEXT_MUTED).pack(side="left")
        self.name_entry = RoundedEntry(name_row, width=200, height=36, radius=12,
                                        font=T.FONT_BODY)
        self.name_entry.pack(side="left", padx=(10, 0))
        self.name_entry.entry.insert(0, self.profile.name)

        # Time window
        time_row = tk.Frame(c, bg=card_bg)
        time_row.pack(fill="x", pady=(0, T.SPACE_SM))

        von_frame = tk.Frame(time_row, bg=card_bg)
        von_frame.pack(side="left")
        tk.Label(von_frame, text="Von", font=T.FONT_MUTED,
                 bg=card_bg, fg=T.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.start_time = TimeInput(von_frame, self.profile.schedule.start_hour,
                                    self.profile.schedule.start_minute)
        self.start_time.pack()

        tk.Label(time_row, text="\u2192", font=(T.FONT, 18),
                 bg=card_bg, fg=T.TEXT_MUTED).pack(side="left", padx=18, pady=(14, 0))

        bis_frame = tk.Frame(time_row, bg=card_bg)
        bis_frame.pack(side="left")
        tk.Label(bis_frame, text="Bis", font=T.FONT_MUTED,
                 bg=card_bg, fg=T.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.end_time = TimeInput(bis_frame, self.profile.schedule.end_hour,
                                  self.profile.schedule.end_minute)
        self.end_time.pack()

        # ---- Collapsible Sub-Sections ----

        # 1. Schlummer-Intervall
        snooze_val = self.profile.snooze_minutes or self.config.snooze_minutes
        snooze_section = CollapsibleSection(
            c, "Schlummer-Intervall", subtitle=f"{snooze_val} min",
            bg=card_bg, header_font=T.FONT_LABEL)
        snooze_section.pack(fill="x", pady=(T.SPACE_MD, 0))
        self._snooze_section = snooze_section
        self.snooze_input = NumberInput(snooze_section.content, value=snooze_val,
                                         min_val=1, max_val=999, suffix="Minuten")
        self.snooze_input.pack(anchor="w", pady=(0, T.SPACE_SM))

        # 2. Website-Trigger
        self._sites_section = CollapsibleSection(
            c, "Website-Trigger", count=len(self._site_triggers),
            bg=card_bg, header_font=T.FONT_LABEL)
        self._sites_section.pack(fill="x", pady=(T.SPACE_MD, 0))
        sc = self._sites_section.content

        self._sites_list_frame = tk.Frame(sc, bg=card_bg)
        self._sites_list_frame.pack(fill="x", pady=(0, T.SPACE_SM))
        self._sites_inner = self._sites_list_frame
        self._rebuild_sites_list()

        add_site_row = tk.Frame(sc, bg=card_bg)
        add_site_row.pack(fill="x")
        self._site_entry = RoundedEntry(
            add_site_row, width=240, height=36, radius=12, font=T.FONT_BODY)
        self._site_entry.pack(side="left")
        self._site_entry.entry.insert(0, "website.com")
        self._site_entry.entry.bind("<FocusIn>", self._site_entry_focus_in)
        self._site_entry.entry.bind("<Return>", lambda e: self._add_site())
        RoundedButton(
            add_site_row, text="+ Hinzufügen",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._add_site,
            width=130, height=36, radius=12, font=T.FONT_BUTTON,
        ).pack(side="left", padx=(8, 0))

        # 3. App-Trigger
        self._apps_section = CollapsibleSection(
            c, "App-Trigger", count=len(self._app_triggers),
            bg=card_bg, header_font=T.FONT_LABEL)
        self._apps_section.pack(fill="x", pady=(T.SPACE_MD, 0))
        ac = self._apps_section.content

        self._apps_list_frame = tk.Frame(ac, bg=card_bg)
        self._apps_list_frame.pack(fill="x", pady=(0, T.SPACE_SM))
        self._apps_inner = self._apps_list_frame
        self._rebuild_apps_list()

        add_app_row = tk.Frame(ac, bg=card_bg)
        add_app_row.pack(fill="x")
        self._app_entry = RoundedEntry(
            add_app_row, width=220, height=36, radius=12, font=T.FONT_BODY)
        self._app_entry.pack(side="left")
        self._app_entry.entry.insert(0, "prozess.exe")
        self._app_entry.entry.bind("<FocusIn>", self._app_entry_focus_in)
        self._app_entry.entry.bind("<Return>", lambda e: self._add_app())
        RoundedButton(
            add_app_row, text="+ Hinzufügen",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._add_app,
            width=130, height=36, radius=12, font=T.FONT_BUTTON,
        ).pack(side="left", padx=(8, 0))
        RoundedButton(
            add_app_row, text="\u2026",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._browse_app,
            width=36, height=36, radius=12, font=T.FONT_BUTTON,
        ).pack(side="left", padx=(6, 0))

        # 4. Alarm-Texte anpassen
        has_overrides = bool(self.profile.alarm_title or self.profile.alarm_message)
        n_overrides = sum(1 for v in [self.profile.alarm_title, self.profile.alarm_message,
                                       self.profile.snooze_label, self.profile.confirm_label] if v)
        overrides = CollapsibleSection(
            c, "Alarm-Texte anpassen", count=n_overrides,
            initially_open=has_overrides, bg=card_bg, header_font=T.FONT_LABEL)
        overrides.pack(fill="x", pady=(T.SPACE_MD, 0))
        oc = overrides.content

        tk.Label(oc, text="Alarm-Titel (optional)", font=T.FONT_MUTED,
                 bg=card_bg, fg=T.TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        self.alarm_title_entry = RoundedEntry(oc, width=380, height=36, radius=12, font=T.FONT_BODY)
        self.alarm_title_entry.pack(anchor="w", pady=(0, T.SPACE_SM))
        if self.profile.alarm_title:
            self.alarm_title_entry.entry.insert(0, self.profile.alarm_title)
        else:
            self._setup_placeholder(self.alarm_title_entry, self.config.popup_title)

        tk.Label(oc, text="Alarm-Nachricht (optional)", font=T.FONT_MUTED,
                 bg=card_bg, fg=T.TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        self.alarm_message_area = RoundedTextarea(oc, width=380, height=60, radius=12)
        self.alarm_message_area.pack(anchor="w", pady=(0, T.SPACE_SM))
        if self.profile.alarm_message:
            self.alarm_message_area.set_text(self.profile.alarm_message)
        else:
            self._setup_textarea_placeholder(self.alarm_message_area, self.config.popup_text)

        tk.Label(oc, text="Schlummern-Button (optional)", font=T.FONT_MUTED,
                 bg=card_bg, fg=T.TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        self.snooze_label_entry = RoundedEntry(oc, width=250, height=36, radius=12, font=T.FONT_BODY)
        self.snooze_label_entry.pack(anchor="w", pady=(0, T.SPACE_SM))
        if self.profile.snooze_label:
            self.snooze_label_entry.entry.insert(0, self.profile.snooze_label)
        else:
            self._setup_placeholder(self.snooze_label_entry, self.config.snooze_label)

        tk.Label(oc, text="Bestätigen-Button (optional)", font=T.FONT_MUTED,
                 bg=card_bg, fg=T.TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        self.confirm_label_entry = RoundedEntry(oc, width=250, height=36, radius=12, font=T.FONT_BODY)
        self.confirm_label_entry.pack(anchor="w")
        if self.profile.confirm_label:
            self.confirm_label_entry.entry.insert(0, self.profile.confirm_label)
        else:
            self._setup_placeholder(self.confirm_label_entry, self.config.confirm_label)

        # 5. Auto-Start Apps
        self._launch_apps = list(self.profile.launch_apps)
        self._launch_section = CollapsibleSection(
            c, "Auto-Start Apps", count=len(self._launch_apps),
            bg=card_bg, header_font=T.FONT_LABEL)
        self._launch_section.pack(fill="x", pady=(T.SPACE_MD, 0))
        lc = self._launch_section.content

        tk.Label(lc, text="Apps die nach Bestätigung gestartet werden",
                 font=T.FONT_MUTED, bg=card_bg, fg=T.TEXT_MUTED,
                 justify="left").pack(anchor="w", pady=(0, T.SPACE_SM))

        self._launch_list_frame = tk.Frame(lc, bg=card_bg)
        self._launch_list_frame.pack(fill="x", pady=(0, T.SPACE_SM))
        self._launch_inner = self._launch_list_frame
        self._rebuild_launch_list()

        add_launch_row = tk.Frame(lc, bg=card_bg)
        add_launch_row.pack(fill="x")
        self._launch_entry = RoundedEntry(
            add_launch_row, width=220, height=36, radius=12, font=T.FONT_BODY)
        self._launch_entry.pack(side="left")
        self._launch_entry.entry.insert(0, "app.exe")
        self._launch_entry.entry.bind("<FocusIn>", self._launch_entry_focus_in)
        self._launch_entry.entry.bind("<Return>", lambda e: self._add_launch_app())
        RoundedButton(
            add_launch_row, text="+ Hinzufügen",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._add_launch_app,
            width=130, height=36, radius=12, font=T.FONT_BUTTON,
        ).pack(side="left", padx=(8, 0))
        RoundedButton(
            add_launch_row, text="\u2026",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._browse_launch_app,
            width=36, height=36, radius=12, font=T.FONT_BUTTON,
        ).pack(side="left", padx=(6, 0))

    # -- Site trigger methods --
    def _rebuild_sites_list(self):
        for w in self._sites_inner.winfo_children():
            w.destroy()
        self._sites_section.update_count(len(self._site_triggers))
        if not self._site_triggers:
            tk.Label(self._sites_inner, text="Keine Websites konfiguriert",
                     font=T.FONT_MUTED, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(padx=10, pady=10)
            return
        for name in self._site_triggers:
            _TriggerRow(self._sites_inner, name,
                        on_remove=self._remove_site, bg=T.BG_CARD).pack(fill="x")

    def _add_site(self):
        name = self._site_entry.get().strip().lower()
        if not name or name == "website.com":
            return
        name = name.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        if name not in [s.lower() for s in self._site_triggers]:
            self._site_triggers.append(name)
            self._rebuild_sites_list()
        self._site_entry.entry.delete(0, "end")

    def _remove_site(self, name):
        self._site_triggers = [s for s in self._site_triggers if s != name]
        self._rebuild_sites_list()

    def _site_entry_focus_in(self, _e):
        if self._site_entry.get() == "website.com":
            self._site_entry.entry.delete(0, "end")

    # -- App trigger methods --
    def _rebuild_apps_list(self):
        for w in self._apps_inner.winfo_children():
            w.destroy()
        self._apps_section.update_count(len(self._app_triggers))
        if not self._app_triggers:
            tk.Label(self._apps_inner, text="Keine Apps konfiguriert",
                     font=T.FONT_MUTED, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(padx=10, pady=10)
            return
        for name in self._app_triggers:
            _TriggerRow(self._apps_inner, name,
                        on_remove=self._remove_app, bg=T.BG_CARD).pack(fill="x")

    def _add_app(self):
        name = self._app_entry.get().strip()
        if not name or name == "prozess.exe":
            return
        if not name.lower().endswith(".exe"):
            name += ".exe"
        if name.lower() not in [a.lower() for a in self._app_triggers]:
            self._app_triggers.append(name)
            self._rebuild_apps_list()
        self._app_entry.entry.delete(0, "end")

    def _remove_app(self, name):
        self._app_triggers = [a for a in self._app_triggers if a != name]
        self._rebuild_apps_list()

    def _app_entry_focus_in(self, _e):
        if self._app_entry.get() == "prozess.exe":
            self._app_entry.entry.delete(0, "end")

    def _browse_app(self):
        top = self.winfo_toplevel()
        top.attributes("-topmost", False)
        path = filedialog.askopenfilename(
            title="App auswählen",
            filetypes=[("Programme", "*.exe"), ("Alle Dateien", "*.*")])
        top.attributes("-topmost", True)
        if path:
            name = os.path.basename(path)
            if name.lower() not in [a.lower() for a in self._app_triggers]:
                self._app_triggers.append(name)
                self._rebuild_apps_list()

    # -- Launch app methods --
    def _rebuild_launch_list(self):
        for w in self._launch_inner.winfo_children():
            w.destroy()
        self._launch_section.update_count(len(self._launch_apps))
        if not self._launch_apps:
            tk.Label(self._launch_inner, text="Keine Apps konfiguriert",
                     font=T.FONT_MUTED, bg=T.BG_CARD, fg=T.TEXT_MUTED).pack(padx=10, pady=10)
            return
        for app_path in self._launch_apps:
            display = os.path.basename(app_path)
            _TriggerRow(self._launch_inner, display,
                        on_remove=lambda n, p=app_path: self._remove_launch_app(p),
                        bg=T.BG_CARD).pack(fill="x")

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
        top = self.winfo_toplevel()
        top.attributes("-topmost", False)
        path = filedialog.askopenfilename(
            title="App auswählen",
            filetypes=[("Programme & Verknüpfungen", "*.exe;*.lnk"), ("Alle Dateien", "*.*")])
        top.attributes("-topmost", True)
        if path and path not in self._launch_apps:
            self._launch_apps.append(path)
            self._rebuild_launch_list()

    def _remove_launch_app(self, app_path):
        self._launch_apps = [p for p in self._launch_apps if p != app_path]
        self._rebuild_launch_list()

    def collect(self):
        """Return (ScheduleProfile, list[TriggerEntry]) from card state."""
        # Get values, filtering out placeholders
        alarm_title = self.alarm_title_entry.get().strip()
        if hasattr(self.alarm_title_entry, '_placeholder') and alarm_title == self.alarm_title_entry._placeholder:
            alarm_title = ""

        alarm_message = self.alarm_message_area.get_text().strip()
        if hasattr(self.alarm_message_area, '_placeholder') and alarm_message == self.alarm_message_area._placeholder:
            alarm_message = ""

        snooze_lbl = self.snooze_label_entry.get().strip()
        if hasattr(self.snooze_label_entry, '_placeholder') and snooze_lbl == self.snooze_label_entry._placeholder:
            snooze_lbl = ""

        confirm_lbl = self.confirm_label_entry.get().strip()
        if hasattr(self.confirm_label_entry, '_placeholder') and confirm_lbl == self.confirm_label_entry._placeholder:
            confirm_lbl = ""

        profile = ScheduleProfile(
            id=self.profile.id,
            name=self.name_entry.get().strip() or "Profil",
            schedule=TriggerSchedule(
                start_hour=self.start_time.hour,
                start_minute=self.start_time.minute,
                end_hour=self.end_time.hour,
                end_minute=self.end_time.minute,
            ),
            snooze_minutes=self.snooze_input.get(),
            alarm_title=alarm_title,
            alarm_message=alarm_message,
            snooze_label=snooze_lbl,
            confirm_label=confirm_lbl,
            launch_apps=list(self._launch_apps),
        )
        triggers = []
        for site in self._site_triggers:
            triggers.append(TriggerEntry(name=site, type="site", profile_id=profile.id))
        for app in self._app_triggers:
            triggers.append(TriggerEntry(name=app, type="app", profile_id=profile.id))
        return profile, triggers


# ====================================================================
# Main Settings Window
# ====================================================================

class SettingsWindow:
    def __init__(self, root: tk.Tk, config: Config, on_save=None, on_test=None, break_scheduler=None):
        self.root = root
        self.config = config
        self.on_save = on_save
        self.on_test = on_test
        self.break_scheduler = break_scheduler
        self.window = None
        self._break_countdown_id = None
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

        w, h = 520, 860
        sx = self.window.winfo_screenwidth()
        sy = self.window.winfo_screenheight()
        max_w = min(800, sx - 100)
        max_h = min(1000, sy - 100)
        self.window.maxsize(max_w, max_h)
        self.window.geometry(f"{w}x{h}+{(sx-w)//2}+{(sy-h)//2}")

        self.window.update_idletasks()
        _enable_dark_titlebar(self.window)

        # -- Bottom buttons (pinned) --
        btn_bar = tk.Frame(self.window, bg=T.BG)
        btn_bar.pack(fill="x", side="bottom", padx=T.SPACE_XL, pady=(16, 24))

        tk.Frame(btn_bar, bg=T.SEPARATOR_COLOR, height=1).pack(fill="x", pady=(0, 16))

        btn_inner = tk.Frame(btn_bar, bg=T.BG)
        btn_inner.pack(fill="x")

        self._test_btn = RoundedButton(
            btn_inner, text="Alarm testen",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._on_test,
            width=195, height=52, radius=22,
        )
        self._test_btn.pack(side="left")

        self._save_btn = RoundedButton(
            btn_inner, text="Speichern",
            bg=T.ACCENT, fg=T.BG,
            hover_bg=T.ACCENT_HOVER, hover_fg=T.BG,
            command=self._on_save,
            width=195, height=52, radius=22,
        )
        self._save_btn.pack(side="right")

        # -- Scrollable content area --
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
            # Only scroll if content is taller than canvas
            bbox = self._canvas.bbox("all")
            if bbox and (bbox[3] - bbox[1]) > self._canvas.winfo_height():
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
        content.pack(fill="both", expand=True, padx=T.SPACE_XL, pady=(T.SPACE_XL, 28))

        # ============================================
        # 1. Schedule Profiles
        # ============================================
        _section_label(content, "Zeitprofile")

        self._profiles_frame = tk.Frame(content, bg=T.BG)
        self._profiles_frame.pack(fill="x", pady=(0, 8))
        self._profile_cards = []
        self._rebuild_profile_cards()

        RoundedButton(
            content, text="+ Profil hinzufügen",
            bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._add_profile,
            width=180, height=40, radius=16, font=T.FONT_BUTTON,
        ).pack(anchor="w", pady=(0, 24))

        _separator(content)

        # ============================================
        # 2. Alarm-Sound
        # ============================================
        self._windows_sounds = _get_windows_sounds()
        self._custom_sounds = list(self.config.custom_sounds)
        self._selected_sound = self.config.sound_file
        self._sound_popup = None

        if not self._selected_sound and self._windows_sounds:
            alarm_sounds = [s for s in self._windows_sounds
                            if "alarm" in os.path.basename(s).lower()]
            self._selected_sound = (alarm_sounds[0] if alarm_sounds
                                    else self._windows_sounds[0])

        sound_section = CollapsibleSection(content, "Alarm-Sound", bg=T.BG)
        sound_section.pack(fill="x", pady=(0, 8))

        sound_row = tk.Frame(sound_section.content, bg=T.BG)
        sound_row.pack(fill="x", pady=(0, T.SPACE_SM))

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

        # ============================================
        # 3. Alarm-Anzeige
        # ============================================
        display_section = CollapsibleSection(content, "Alarm-Anzeige", bg=T.BG)
        display_section.pack(fill="x", pady=(0, 8))

        self.fullscreen_var = tk.BooleanVar(value=self.config.fullscreen_popup)
        CustomCheckbox(display_section.content,
                       "Fullscreen-Alarm (ganzer Bildschirm, kein Wegklicken)",
                       self.fullscreen_var).pack(anchor="w", pady=(0, T.SPACE_SM))

        _separator(content)

        # ============================================
        # 3.5 Pausentimer
        # ============================================
        break_sub = "Alle {} min / {} min Pause".format(
            self.config.break_interval_minutes,
            self.config.break_duration_minutes,
        ) if self.config.break_enabled else "Deaktiviert"
        self._break_section = CollapsibleSection(
            content, "Pausentimer", subtitle=break_sub, bg=T.BG)
        self._break_section.pack(fill="x", pady=(0, 8))

        self.break_enabled_var = tk.BooleanVar(value=self.config.break_enabled)
        CustomCheckbox(self._break_section.content, "Pausentimer aktivieren",
                       self.break_enabled_var).pack(anchor="w", pady=(0, T.SPACE_SM))

        # Live countdown to next break
        self._break_countdown_label = tk.Label(
            self._break_section.content, text="",
            font=T.FONT_MUTED, bg=T.BG, fg=T.TEXT_MUTED, anchor="w")
        self._break_countdown_label.pack(anchor="w", pady=(0, T.SPACE_SM))

        interval_row = tk.Frame(self._break_section.content, bg=T.BG)
        interval_row.pack(fill="x", pady=(0, T.SPACE_SM))
        tk.Label(interval_row, text="Arbeitsintervall",
                 font=T.FONT_BODY, bg=T.BG, fg=T.TEXT_MUTED).pack(side="left", padx=(0, 12))
        self._break_interval = NumberInput(
            interval_row, value=self.config.break_interval_minutes,
            min_val=1, max_val=240, suffix="min")
        self._break_interval.pack(side="left")

        duration_row = tk.Frame(self._break_section.content, bg=T.BG)
        duration_row.pack(fill="x", pady=(0, T.SPACE_SM))
        tk.Label(duration_row, text="Pausendauer",
                 font=T.FONT_BODY, bg=T.BG, fg=T.TEXT_MUTED).pack(side="left", padx=(0, 12))
        self._break_duration = NumberInput(
            duration_row, value=self.config.break_duration_minutes,
            min_val=1, max_val=30, suffix="min")
        self._break_duration.pack(side="left")

        snooze_row = tk.Frame(self._break_section.content, bg=T.BG)
        snooze_row.pack(fill="x", pady=(0, T.SPACE_SM))
        tk.Label(snooze_row, text="Schlummer",
                 font=T.FONT_BODY, bg=T.BG, fg=T.TEXT_MUTED).pack(side="left", padx=(0, 12))
        self._break_snooze = NumberInput(
            snooze_row, value=self.config.break_snooze_minutes,
            min_val=1, max_val=30, suffix="min")
        self._break_snooze.pack(side="left")

        # Break title
        title_row = tk.Frame(self._break_section.content, bg=T.BG)
        title_row.pack(fill="x", pady=(0, T.SPACE_SM))
        tk.Label(title_row, text="Titel",
                 font=T.FONT_BODY, bg=T.BG, fg=T.TEXT_MUTED).pack(side="left", padx=(0, 12))
        self._break_title_entry = RoundedEntry(
            title_row, width=240, height=36, radius=12, font=T.FONT_BODY)
        self._break_title_entry.pack(side="left")
        self._break_title_entry.entry.insert(0, self.config.break_popup_title)

        # Break icon picker
        icon_row = tk.Frame(self._break_section.content, bg=T.BG)
        icon_row.pack(fill="x", pady=(0, T.SPACE_SM))
        tk.Label(icon_row, text="Icon",
                 font=T.FONT_BODY, bg=T.BG, fg=T.TEXT_MUTED).pack(side="left", padx=(0, 12))
        self._break_icon_picker = EmojiPicker(icon_row)
        self._break_icon_picker.set(self.config.break_icon)
        self._break_icon_picker.pack(side="left")

        # Break text
        tk.Label(self._break_section.content, text="Nachricht",
                 font=T.FONT_BODY, bg=T.BG, fg=T.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(0, 4))
        self._break_text_entry = RoundedTextarea(
            self._break_section.content, width=380, height=70, radius=12)
        self._break_text_entry.pack(fill="x", pady=(0, T.SPACE_SM))
        self._break_text_entry.set_text(self.config.break_popup_text)

        self.break_fullscreen_var = tk.BooleanVar(value=self.config.break_fullscreen)
        CustomCheckbox(self._break_section.content,
                       "Fullscreen (ganzer Bildschirm)",
                       self.break_fullscreen_var).pack(anchor="w", pady=(0, T.SPACE_SM))

        _separator(content)

        # ============================================
        # 4. Autostart
        # ============================================
        autostart_section = CollapsibleSection(content, "Autostart", bg=T.BG)
        autostart_section.pack(fill="x", pady=(0, 8))

        self.autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        CustomCheckbox(autostart_section.content, "Mit Windows starten",
                       self.autostart_var).pack(anchor="w", pady=(0, T.SPACE_SM))

        # Fade-in
        fade_in_window(self.window, duration_ms=250)
        self._update_break_countdown()

    # -- Profile Cards --

    def _rebuild_profile_cards(self):
        for w in self._profiles_frame.winfo_children():
            w.destroy()
        self._profile_cards = []
        deletable = len(self.config.schedule_profiles) > 1
        for profile in self.config.schedule_profiles:
            triggers = self.config.get_triggers_for_profile(profile.id)
            card = _ProfileCard(self._profiles_frame, profile, triggers, self.config,
                                on_delete=self._delete_profile,
                                deletable=deletable)
            card.pack(fill="x", pady=(0, T.CARD_GAP + 4))
            self._profile_cards.append(card)

    def _add_profile(self):
        new_profile = ScheduleProfile(
            name=f"Profil {len(self.config.schedule_profiles) + 1}")
        self.config.schedule_profiles.append(new_profile)
        self._rebuild_profile_cards()

    def _delete_profile(self, profile_id):
        if len(self.config.schedule_profiles) <= 1:
            return
        self.config.schedule_profiles = [
            p for p in self.config.schedule_profiles if p.id != profile_id
        ]
        self._rebuild_profile_cards()

    # -- Scroll / Canvas --

    def _on_scroll_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

    # ================================================
    # Sound Picker (Dropdown)
    # ================================================

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
        popup.configure(bg=T.BG_INPUT)
        self._sound_popup = popup

        self._sound_dropdown.update_idletasks()
        x = self._sound_dropdown.winfo_rootx()
        y = (self._sound_dropdown.winfo_rooty()
             + self._sound_dropdown.winfo_height() + 4)
        w = self._sound_dropdown.winfo_width()

        row_h = 40
        max_visible = 8
        total_sounds = len(self._windows_sounds) + len(self._custom_sounds)
        if self._custom_sounds:
            total_sounds += 1
        visible_rows = min(max(total_sounds, 1), max_visible)
        popup_h = visible_rows * row_h + 2

        popup.geometry(f"{w}x{popup_h}+{x}+{y}")

        inner = tk.Frame(popup, bg=T.BG)
        inner.pack(fill="both", expand=True, padx=0, pady=0)

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

        def _on_mousewheel(event):
            sp_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        for w_bind in (popup, sp_canvas, scroll_frame):
            w_bind.bind("<MouseWheel>", _on_mousewheel)

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

        popup.update_idletasks()
        self._scroll_to_selected(scroll_frame, sp_canvas)

        popup.bind("<Deactivate>",
                   lambda e: self.window.after(100, self._close_sound_popup))
        popup.bind("<Escape>", lambda e: self._close_sound_popup())
        popup.focus_set()

    def _scroll_to_selected(self, scroll_frame, canvas):
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
        if (hasattr(self, "_sound_play_btn")
                and self.window and self.window.winfo_exists()):
            self._sound_play_btn.itemconfigure(
                self._sound_play_btn._label, text="\u25b6")

    def _play_preview(self, filepath, on_done_callback):
        self._stop_preview()
        self._playing_sound = True
        try:
            winsound.PlaySound(
                filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            self._playing_sound = False
            return
        duration_ms = self._get_wav_duration_ms(filepath)
        if duration_ms and self.window and self.window.winfo_exists():
            self._play_done_id = self.window.after(
                duration_ms, self._on_play_finished, on_done_callback)

    def _get_wav_duration_ms(self, filepath):
        try:
            with wave.open(filepath, "r") as w:
                return int((w.getnframes() / w.getframerate()) * 1000)
        except Exception:
            return 3000

    def _on_play_finished(self, callback):
        self._playing_sound = False
        if callback:
            callback()

    def _stop_preview(self):
        if hasattr(self, "_play_done_id") and self._play_done_id:
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
        if (path and path not in self._custom_sounds
                and path not in self._windows_sounds):
            self._custom_sounds.append(path)
            self._selected_sound = path
            self._draw_sound_dropdown()

    # ================================================
    # Save / Close
    # ================================================

    def _on_save(self):
        self._stop_preview()
        self._do_save()
        # Visual feedback
        self._save_btn.itemconfigure(self._save_btn._rect, fill=T.SUCCESS)
        self._save_btn.itemconfigure(self._save_btn._label, text="✓", fill=T.BG)
        self.window.after(800, self._reset_save_btn)

    def _reset_save_btn(self):
        if self.window and self.window.winfo_exists():
            self._save_btn._cur_bg = T.ACCENT
            self._save_btn.itemconfigure(self._save_btn._rect, fill=T.ACCENT)
            self._save_btn.itemconfigure(self._save_btn._label, text="Speichern", fill=T.BG)

    def _do_save(self):
        profiles = []
        all_triggers = []
        for card in self._profile_cards:
            profile, triggers = card.collect()
            profiles.append(profile)
            all_triggers.extend(triggers)
        self.config.schedule_profiles = profiles
        self.config.triggers = all_triggers

        self.config.fullscreen_popup = self.fullscreen_var.get()
        self.config.custom_sounds = list(self._custom_sounds)
        self.config.sound_file = self._selected_sound or ""

        if self.autostart_var.get():
            enable_autostart()
        else:
            disable_autostart()
        self.config.autostart = self.autostart_var.get()

        self.config.break_enabled = self.break_enabled_var.get()
        self.config.break_interval_minutes = self._break_interval.get()
        self.config.break_duration_minutes = self._break_duration.get()
        self.config.break_snooze_minutes = self._break_snooze.get()
        self.config.break_popup_title = self._break_title_entry.get().strip() or "Pause"
        self.config.break_popup_text = self._break_text_entry.get_text().strip() or "Steh auf, streck dich, trink Wasser."
        self.config.break_fullscreen = self.break_fullscreen_var.get()
        self.config.break_icon = self._break_icon_picker.get() or "☕"

        # Update subtitle
        if self.config.break_enabled:
            sub = "Alle {} min / {} min Pause".format(
                self.config.break_interval_minutes,
                self.config.break_duration_minutes)
        else:
            sub = "Deaktiviert"
        self._break_section.update_subtitle(sub)

        self.config.save()
        if self.on_save:
            self.on_save()

    def _on_test(self):
        self._stop_preview()
        if self.on_test:
            self.on_test()

    def _update_break_countdown(self):
        """Update the live countdown label for the break timer."""
        if not self.window or not self.window.winfo_exists():
            self._break_countdown_id = None
            return
        if self.break_scheduler and self.break_scheduler.config.break_enabled:
            from break_scheduler import BreakState
            state = self.break_scheduler.state
            remaining = self.break_scheduler.remaining_until_break_seconds()
            if state == BreakState.RUNNING and remaining > 0:
                mins, secs = divmod(remaining, 60)
                self._break_countdown_label.configure(
                    text=f"Nächste Pause in {mins:02d}:{secs:02d}")
            elif state == BreakState.BREAK_ACTIVE:
                br = self.break_scheduler.remaining_break_seconds()
                mins, secs = divmod(br, 60)
                self._break_countdown_label.configure(
                    text=f"Pause läuft: {mins:02d}:{secs:02d}")
            elif state == BreakState.SNOOZED and remaining > 0:
                mins, secs = divmod(remaining, 60)
                self._break_countdown_label.configure(
                    text=f"Schlummert: {mins:02d}:{secs:02d}")
            elif state == BreakState.BREAK_DUE:
                self._break_countdown_label.configure(text="Pause fällig")
            else:
                self._break_countdown_label.configure(text="")
        else:
            self._break_countdown_label.configure(text="")
        self._break_countdown_id = self.window.after(1000, self._update_break_countdown)

    def _close(self):
        if self._break_countdown_id:
            try:
                self.window.after_cancel(self._break_countdown_id)
            except Exception:
                pass
            self._break_countdown_id = None
        self._stop_preview()
        self._close_sound_popup()
        try:
            self.window.unbind_all("<MouseWheel>")
        except Exception:
            pass
        if self.window and self.window.winfo_exists():
            self.window.destroy()
