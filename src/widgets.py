"""Reusable custom widgets — smooth Apple-like styling with animations."""

import tkinter as tk
import theme as T


# ---------------------------------------------------------------------------
# Canvas helpers
# ---------------------------------------------------------------------------

def round_rect(canvas, x1, y1, x2, y2, radius=12, **kwargs):
    """Draw a rounded rectangle on a canvas."""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1, x2, y1 + radius,
        x2, y2 - radius,
        x2, y2, x2 - radius, y2,
        x1 + radius, y2,
        x1, y2, x1, y2 - radius,
        x1, y1 + radius,
        x1, y1, x1 + radius, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def _lerp_color(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex colors. t=0 -> c1, t=1 -> c2."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# Fade-in animation mixin
# ---------------------------------------------------------------------------

def fade_in_window(window, duration_ms=300, steps=15, on_done=None):
    """Animate a window from 0 to full opacity."""
    window.attributes("-alpha", 0.0)
    step_time = duration_ms // steps

    def _step(i):
        if not window.winfo_exists():
            return
        alpha = i / steps
        window.attributes("-alpha", alpha)
        if i < steps:
            window.after(step_time, _step, i + 1)
        elif on_done:
            on_done()

    window.after(10, _step, 0)


# ---------------------------------------------------------------------------
# Rounded Button with smooth hover transition
# ---------------------------------------------------------------------------

class RoundedButton(tk.Canvas):
    """Button with rounded corners, smooth color transitions and press effect."""

    def __init__(self, parent, text, bg, fg, command,
                 hover_bg=None, hover_fg=None,
                 font=None, width=200, height=48, radius=14):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg"), highlightthickness=0, bd=0)

        self._bg = bg
        self._fg = fg
        self._hover_bg = hover_bg or bg
        self._hover_fg = hover_fg or fg
        self._cur_bg = bg
        self._command = command
        self._radius = radius
        self._width = width
        self._height = height
        self._font = font or T.FONT_BUTTON_LG
        self._anim_id = None
        self._pressed = False

        self._rect = round_rect(self, 1, 1, width - 1, height - 1, radius,
                                fill=bg, outline="")
        self._label = self.create_text(
            width // 2, height // 2, text=text, fill=fg, font=self._font)

        for tag in ("<Enter>", "<Leave>", "<Button-1>", "<ButtonRelease-1>"):
            self.bind(tag, getattr(self, f"_on_{tag.strip('<>').lower().replace('-', '_')}"))
            self.tag_bind(self._rect, tag,
                          getattr(self, f"_on_{tag.strip('<>').lower().replace('-', '_')}"))
            self.tag_bind(self._label, tag,
                          getattr(self, f"_on_{tag.strip('<>').lower().replace('-', '_')}"))

        self.configure(cursor="hand2")

    def _animate_to(self, target_bg, target_fg, steps=8):
        if self._anim_id:
            self.after_cancel(self._anim_id)
        start_bg = self._cur_bg

        def _step(i):
            if not self.winfo_exists():
                return
            t = i / steps
            c = _lerp_color(start_bg, target_bg, t)
            self._cur_bg = c
            self.itemconfigure(self._rect, fill=c)
            if i < steps:
                self._anim_id = self.after(18, _step, i + 1)
            else:
                self.itemconfigure(self._label, fill=target_fg)

        self.itemconfigure(self._label, fill=target_fg)
        _step(0)

    def _on_enter(self, _e):
        self._animate_to(self._hover_bg, self._hover_fg)

    def _on_leave(self, _e):
        self._pressed = False
        self._animate_to(self._bg, self._fg)

    def _on_button_1(self, _e):
        self._pressed = True
        self.move(self._label, 0, 1)

    def _on_buttonrelease_1(self, _e):
        if self._pressed:
            self._pressed = False
            self.move(self._label, 0, -1)
            if self._command:
                self._command()


# ---------------------------------------------------------------------------
# Rounded Entry
# ---------------------------------------------------------------------------

class RoundedEntry(tk.Canvas):
    """Entry with rounded border and focus glow animation."""

    def __init__(self, parent, textvariable=None, width=200, height=48,
                 radius=12, readonly=False, justify="left", font=None):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg"), highlightthickness=0, bd=0)

        self._rect = round_rect(self, 1, 1, width - 1, height - 1, radius,
                                fill=T.BG_INPUT, outline=T.BORDER)

        self.entry = tk.Entry(
            self, textvariable=textvariable,
            font=font or T.FONT_INPUT,
            bg=T.BG_INPUT, fg=T.TEXT, insertbackground=T.TEXT,
            relief="flat", bd=0, highlightthickness=0,
            justify=justify,
            state="readonly" if readonly else "normal",
            readonlybackground=T.BG_INPUT,
        )
        self.create_window(width // 2, height // 2, window=self.entry,
                           width=width - 28, height=height - 16)

        # Focus glow
        self.entry.bind("<FocusIn>", lambda e: self.itemconfigure(
            self._rect, outline=T.BORDER_FOCUS))
        self.entry.bind("<FocusOut>", lambda e: self.itemconfigure(
            self._rect, outline=T.BORDER))

    def get(self):
        return self.entry.get()


# ---------------------------------------------------------------------------
# Rounded Textarea
# ---------------------------------------------------------------------------

class RoundedTextarea(tk.Canvas):
    """Multi-line text field with rounded border and focus glow."""

    def __init__(self, parent, width=380, height=80, radius=12):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg"), highlightthickness=0, bd=0)

        self._rect = round_rect(self, 1, 1, width - 1, height - 1, radius,
                                fill=T.BG_INPUT, outline=T.BORDER)

        self.text = tk.Text(
            self, font=T.FONT_BODY_LG, bg=T.BG_INPUT, fg=T.TEXT,
            insertbackground=T.TEXT, relief="flat", bd=0,
            highlightthickness=0, wrap="word", undo=True,
        )
        self.create_window(width // 2, height // 2, window=self.text,
                           width=width - 24, height=height - 16)

        self.text.bind("<FocusIn>", lambda e: self.itemconfigure(
            self._rect, outline=T.BORDER_FOCUS))
        self.text.bind("<FocusOut>", lambda e: self.itemconfigure(
            self._rect, outline=T.BORDER))

    def get_text(self) -> str:
        return self.text.get("1.0", "end-1c")

    def set_text(self, val: str):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", val)


# ---------------------------------------------------------------------------
# Number Input (free entry with up/down)
# ---------------------------------------------------------------------------

class NumberInput(tk.Frame):
    """Rounded number input with arrow buttons and keyboard/scroll support."""

    def __init__(self, parent, value=15, min_val=1, max_val=999, suffix="min"):
        super().__init__(parent, bg=parent.cget("bg"))
        self._min = min_val
        self._max = max_val
        self.var = tk.StringVar(value=str(value))

        # Down arrow
        self._down = RoundedButton(
            self, text="\u2212", bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=lambda: self._step(-1),
            width=38, height=42, radius=12, font=(T.FONT, 14),
        )
        self._down.pack(side="left")

        # Entry
        self._entry = RoundedEntry(
            self, textvariable=self.var, width=72, height=42,
            radius=12, justify="center", font=(T.FONT, 16),
        )
        self._entry.pack(side="left", padx=6)
        self._entry.entry.bind("<FocusOut>", lambda e: self._clamp())
        self._entry.entry.bind("<Up>", lambda e: self._step(1))
        self._entry.entry.bind("<Down>", lambda e: self._step(-1))
        self._entry.entry.bind("<MouseWheel>",
                               lambda e: self._step(1 if e.delta > 0 else -1))

        # Up arrow
        self._up = RoundedButton(
            self, text="+", bg=T.BG_INPUT, fg=T.TEXT_SECONDARY,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=lambda: self._step(1),
            width=38, height=42, radius=12, font=(T.FONT, 14),
        )
        self._up.pack(side="left")

        # Suffix
        tk.Label(self, text=suffix, font=T.FONT_BODY_LG,
                 bg=self.cget("bg"), fg=T.TEXT_MUTED).pack(side="left", padx=(8, 0))

    def _clamp(self):
        try:
            v = max(self._min, min(self._max, int(self.var.get())))
        except ValueError:
            v = self._min
        self.var.set(str(v))

    def _step(self, delta):
        self._clamp()
        v = max(self._min, min(self._max, int(self.var.get()) + delta))
        self.var.set(str(v))

    def get(self) -> int:
        self._clamp()
        return int(self.var.get())


# ---------------------------------------------------------------------------
# Time Input
# ---------------------------------------------------------------------------

class TimeInput(tk.Frame):
    """Custom time input with rounded fields."""

    def __init__(self, parent, hour=0, minute=0):
        super().__init__(parent, bg=parent.cget("bg"))

        self.hour_var = tk.StringVar(value=f"{hour:02d}")
        self.min_var = tk.StringVar(value=f"{minute:02d}")

        self._h = RoundedEntry(self, textvariable=self.hour_var,
                               width=64, height=48, radius=12,
                               justify="center", font=(T.FONT, 18))
        self._h.pack(side="left")
        self._h.entry.bind("<FocusOut>", lambda e: self._clamp_hour())
        self._h.entry.bind("<Up>", lambda e: self._step_hour(1))
        self._h.entry.bind("<Down>", lambda e: self._step_hour(-1))
        self._h.entry.bind("<MouseWheel>",
                           lambda e: self._step_hour(1 if e.delta > 0 else -1))

        tk.Label(self, text=":", font=(T.FONT, 20, "bold"),
                 bg=self.cget("bg"), fg=T.TEXT_MUTED).pack(side="left", padx=8)

        self._m = RoundedEntry(self, textvariable=self.min_var,
                               width=64, height=48, radius=12,
                               justify="center", font=(T.FONT, 18))
        self._m.pack(side="left")
        self._m.entry.bind("<FocusOut>", lambda e: self._clamp_min())
        self._m.entry.bind("<Up>", lambda e: self._step_min(15))
        self._m.entry.bind("<Down>", lambda e: self._step_min(-15))
        self._m.entry.bind("<MouseWheel>",
                           lambda e: self._step_min(15 if e.delta > 0 else -15))

    def _clamp_hour(self):
        try:
            v = int(self.hour_var.get()) % 24
        except ValueError:
            v = 0
        self.hour_var.set(f"{v:02d}")

    def _clamp_min(self):
        try:
            v = int(self.min_var.get()) % 60
        except ValueError:
            v = 0
        self.min_var.set(f"{v:02d}")

    def _step_hour(self, delta):
        try:
            v = (int(self.hour_var.get()) + delta) % 24
        except ValueError:
            v = 0
        self.hour_var.set(f"{v:02d}")

    def _step_min(self, delta):
        try:
            v = (int(self.min_var.get()) + delta) % 60
        except ValueError:
            v = 0
        self.min_var.set(f"{v:02d}")

    @property
    def hour(self) -> int:
        self._clamp_hour()
        return int(self.hour_var.get())

    @property
    def minute(self) -> int:
        self._clamp_min()
        return int(self.min_var.get())


# ---------------------------------------------------------------------------
# Custom Checkbox (rounded, with smooth toggle)
# ---------------------------------------------------------------------------

class CustomCheckbox(tk.Frame):
    """Rounded checkbox with smooth toggle animation."""

    def __init__(self, parent, text, variable):
        super().__init__(parent, bg=parent.cget("bg"), cursor="hand2")
        self.var = variable
        self._anim_id = None

        self.canvas = tk.Canvas(self, width=24, height=24,
                                bg=parent.cget("bg"), highlightthickness=0, bd=0)
        self.canvas.pack(side="left", padx=(0, 12))

        self._rect = round_rect(self.canvas, 0, 0, 24, 24, radius=7,
                                fill=T.BG_INPUT, outline=T.BORDER)
        self._check = self.canvas.create_text(
            12, 12, text="", fill=T.BG, font=(T.FONT, 12, "bold"))

        self.label = tk.Label(self, text=text, font=T.FONT_BODY,
                              bg=parent.cget("bg"), fg=T.TEXT)
        self.label.pack(side="left")

        self._update(animate=False)
        self.canvas.bind("<Button-1>", lambda e: self._toggle())
        self.label.bind("<Button-1>", lambda e: self._toggle())
        self.bind("<Button-1>", lambda e: self._toggle())

    def _toggle(self):
        self.var.set(not self.var.get())
        self._update(animate=True)

    def _update(self, animate=False):
        target_bg = T.TEXT if self.var.get() else T.BG_INPUT
        target_outline = T.TEXT if self.var.get() else T.BORDER
        check_text = "\u2713" if self.var.get() else ""

        if not animate:
            self.canvas.itemconfigure(self._rect, fill=target_bg, outline=target_outline)
            self.canvas.itemconfigure(self._check, text=check_text)
            return

        # Quick color transition
        if self._anim_id:
            self.after_cancel(self._anim_id)

        self.canvas.itemconfigure(self._check, text=check_text)
        start_bg = T.BG_INPUT if self.var.get() else T.TEXT
        steps = 6

        def _step(i):
            if not self.winfo_exists():
                return
            t = i / steps
            c = _lerp_color(start_bg, target_bg, t)
            self.canvas.itemconfigure(self._rect, fill=c, outline=c)
            if i < steps:
                self._anim_id = self.after(20, _step, i + 1)

        _step(0)


# ---------------------------------------------------------------------------
# Auto-hiding Scrollbar — slim overlay, Apple-like
# ---------------------------------------------------------------------------

class AutoHideScrollbar(tk.Canvas):
    """Slim auto-hiding scrollbar overlay. Shows on scroll/hover, hides when
    content fits or after inactivity."""

    def __init__(self, parent, command=None, width=8):
        super().__init__(parent, width=width, bg=T.BG,
                         highlightthickness=0, bd=0)
        self._command = command
        self._bar_width = width
        self._first = 0.0
        self._last = 1.0
        self._visible = False
        self._hide_id = None
        self._drag_start = None
        self._hovering = False
        self._thumb_color = "#3a3a3a"
        self._thumb_hover_color = "#555555"

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def set(self, first, last):
        """Scrollbar protocol — called by target widget on scroll change."""
        self._first = float(first)
        self._last = float(last)

        if self._first <= 0.001 and self._last >= 0.999:
            # All content visible — hide completely
            self._hide()
            return

        self._show()
        self._draw_thumb()
        self._schedule_hide()

    def show_temporarily(self):
        """Show scrollbar briefly (e.g. on hover over scroll area)."""
        if self._first <= 0.001 and self._last >= 0.999:
            return
        self._show()
        self._draw_thumb()
        self._schedule_hide()

    def _draw_thumb(self):
        self.delete("thumb")
        h = self.winfo_height()
        w = self._bar_width
        if h < 20:
            return

        thumb_h = max(30, (self._last - self._first) * h)
        thumb_y = self._first * h
        r = max(2, (w - 2) // 2)
        x1 = 1
        y1 = max(2, int(thumb_y) + 2)
        x2 = w - 1
        y2 = min(h - 2, int(thumb_y + thumb_h) - 2)

        color = self._thumb_hover_color if self._hovering else self._thumb_color
        round_rect(self, x1, y1, x2, y2, radius=r,
                   fill=color, outline="", tags="thumb")

    def _show(self):
        if not self._visible:
            self._visible = True
            self.lift()

    def _hide(self):
        if self._hide_id:
            self.after_cancel(self._hide_id)
            self._hide_id = None
        self._visible = False
        self.delete("thumb")
        self.lower()

    def _schedule_hide(self):
        if self._hide_id:
            self.after_cancel(self._hide_id)
        if not self._hovering and not self._drag_start:
            self._hide_id = self.after(1200, self._hide)

    def _on_enter(self, _e):
        self._hovering = True
        if self._visible:
            self._draw_thumb()
        if self._hide_id:
            self.after_cancel(self._hide_id)
            self._hide_id = None

    def _on_leave(self, _e):
        self._hovering = False
        if self._visible:
            self._draw_thumb()
            self._schedule_hide()

    def _on_press(self, e):
        h = self.winfo_height()
        thumb_h = max(30, (self._last - self._first) * h)
        thumb_y = self._first * h

        if thumb_y <= e.y <= thumb_y + thumb_h:
            # Click on thumb — start drag
            self._drag_start = (e.y, self._first)
        else:
            # Click on track — jump to position
            fraction = max(0.0, min(1.0, e.y / h))
            if self._command:
                self._command("moveto", str(fraction))

    def _on_drag(self, e):
        if self._drag_start is None:
            return
        h = self.winfo_height()
        dy = e.y - self._drag_start[0]
        visible_fraction = self._last - self._first
        new_first = self._drag_start[1] + dy / h
        new_first = max(0.0, min(1.0 - visible_fraction, new_first))
        if self._command:
            self._command("moveto", str(new_first))

    def _on_release(self, _e):
        self._drag_start = None
        self._schedule_hide()
