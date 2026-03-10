"""Reusable custom widgets — premium dark styling with Gold accent and animations."""

import tkinter as tk
import math
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


def ease_in_out(t: float) -> float:
    """Smooth ease-in-out curve (cubic). t in [0,1] -> [0,1]."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2


# ---------------------------------------------------------------------------
# Canvas icon drawing functions
# ---------------------------------------------------------------------------

def draw_checkmark(canvas, cx, cy, size, color, width=2, tag="icon"):
    """Draw a smooth checkmark centered at (cx, cy)."""
    s = size / 2
    points = [cx - s * 0.6, cy, cx - s * 0.1, cy + s * 0.5, cx + s * 0.7, cy - s * 0.4]
    canvas.create_line(points, fill=color, width=width, capstyle="round",
                       joinstyle="round", tags=tag)


def draw_arrow_right(canvas, cx, cy, size, color, tag="icon"):
    """Draw a right-pointing triangle (collapsed state)."""
    s = size / 2
    canvas.create_polygon(
        cx - s * 0.3, cy - s * 0.5,
        cx + s * 0.5, cy,
        cx - s * 0.3, cy + s * 0.5,
        fill=color, outline="", tags=tag)


def draw_arrow_down(canvas, cx, cy, size, color, tag="icon"):
    """Draw a downward-pointing triangle (expanded state)."""
    s = size / 2
    canvas.create_polygon(
        cx - s * 0.5, cy - s * 0.3,
        cx + s * 0.5, cy - s * 0.3,
        cx, cy + s * 0.5,
        fill=color, outline="", tags=tag)


def draw_close_x(canvas, cx, cy, size, color, width=2, tag="icon"):
    """Draw an X icon centered at (cx, cy)."""
    s = size / 2 * 0.6
    canvas.create_line(cx - s, cy - s, cx + s, cy + s,
                       fill=color, width=width, capstyle="round", tags=tag)
    canvas.create_line(cx + s, cy - s, cx - s, cy + s,
                       fill=color, width=width, capstyle="round", tags=tag)


def draw_play(canvas, cx, cy, size, color, tag="icon"):
    """Draw a play triangle."""
    s = size / 2
    canvas.create_polygon(
        cx - s * 0.4, cy - s * 0.6,
        cx + s * 0.6, cy,
        cx - s * 0.4, cy + s * 0.6,
        fill=color, outline="", smooth=False, tags=tag)


def draw_stop(canvas, cx, cy, size, color, tag="icon"):
    """Draw a stop square."""
    s = size / 2 * 0.5
    canvas.create_rectangle(cx - s, cy - s, cx + s, cy + s,
                            fill=color, outline="", tags=tag)


def draw_circular_progress(canvas, cx, cy, radius, thickness, fraction, fg_color, bg_color=None):
    """Draw a smooth anti-aliased circular progress ring using polylines."""
    if bg_color is None:
        bg_color = T.BG_INPUT
    segments = 120

    # Background ring - full circle polyline
    bg_pts = []
    for i in range(segments + 1):
        angle = math.radians(i * 360 / segments - 90)
        bg_pts.extend([cx + radius * math.cos(angle),
                       cy + radius * math.sin(angle)])
    canvas.create_line(bg_pts, fill=bg_color, width=thickness,
                       capstyle="round", joinstyle="round",
                       smooth=True, tags="ring")

    # Foreground arc
    if fraction > 0.003:
        fg_segs = max(6, int(segments * fraction))
        fg_pts = []
        for i in range(fg_segs + 1):
            angle = math.radians(-90 + i * (fraction * 360) / fg_segs)
            fg_pts.extend([cx + radius * math.cos(angle),
                           cy + radius * math.sin(angle)])
        canvas.create_line(fg_pts, fill=fg_color, width=thickness,
                           capstyle="round", joinstyle="round",
                           smooth=True, tags="ring")


# ---------------------------------------------------------------------------
# Fade animations
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


def fade_out_window(window, duration_ms=250, steps=12, on_done=None):
    """Animate a window from current opacity to 0, then call on_done."""
    step_time = duration_ms // steps

    def _step(i):
        if not window.winfo_exists():
            if on_done:
                on_done()
            return
        alpha = 1.0 - (i / steps)
        try:
            window.attributes("-alpha", max(0.0, alpha))
        except Exception:
            if on_done:
                on_done()
            return
        if i < steps:
            window.after(step_time, _step, i + 1)
        else:
            if on_done:
                on_done()

    _step(0)


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
            handler = getattr(self, "_on_" + tag.strip("<>").lower().replace("-", "_"))
            self.bind(tag, handler)
            self.tag_bind(self._rect, tag, handler)
            self.tag_bind(self._label, tag, handler)

        self.configure(cursor="hand2")

    def _animate_to(self, target_bg, target_fg, steps=12):
        if self._anim_id:
            self.after_cancel(self._anim_id)
        start_bg = self._cur_bg

        def _step(i):
            if not self.winfo_exists():
                return
            t = ease_in_out(i / steps)
            c = _lerp_color(start_bg, target_bg, t)
            self._cur_bg = c
            self.itemconfigure(self._rect, fill=c)
            if i < steps:
                self._anim_id = self.after(14, _step, i + 1)
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
        if not self._pressed:
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
                 radius=14, readonly=False, justify="left", font=None):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg"), highlightthickness=0, bd=0)

        self._rect = round_rect(self, 1, 1, width - 1, height - 1, radius,
                                fill=T.BG_INPUT, outline=T.BORDER)

        self.entry = tk.Entry(
            self, textvariable=textvariable,
            font=font or T.FONT_INPUT,
            bg=T.BG_INPUT, fg=T.TEXT, insertbackground=T.ACCENT,
            relief="flat", bd=0, highlightthickness=0,
            justify=justify,
            state="readonly" if readonly else "normal",
            readonlybackground=T.BG_INPUT,
        )
        self.create_window(width // 2, height // 2, window=self.entry,
                           width=width - 28, height=height - 16)

        # Focus glow — Gold ring
        self.entry.bind("<FocusIn>", lambda e: self.itemconfigure(
            self._rect, outline=T.FOCUS_RING))
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
            insertbackground=T.ACCENT, relief="flat", bd=0,
            highlightthickness=0, wrap="word", undo=True,
        )
        self.create_window(width // 2, height // 2, window=self.text,
                           width=width - 24, height=height - 16)

        # Focus glow — Gold ring
        self.text.bind("<FocusIn>", lambda e: self.itemconfigure(
            self._rect, outline=T.FOCUS_RING))
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
# Custom Checkbox (canvas-drawn checkmark, Gold accent)
# ---------------------------------------------------------------------------

class CustomCheckbox(tk.Frame):
    """Rounded checkbox with smooth toggle animation and canvas checkmark."""

    def __init__(self, parent, text, variable):
        super().__init__(parent, bg=parent.cget("bg"), cursor="hand2")
        self.var = variable
        self._anim_id = None

        self.canvas = tk.Canvas(self, width=24, height=24,
                                bg=parent.cget("bg"), highlightthickness=0, bd=0)
        self.canvas.pack(side="left", padx=(0, 12))

        self._rect = round_rect(self.canvas, 0, 0, 24, 24, radius=7,
                                fill=T.BG_INPUT, outline=T.BORDER)

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
        target_bg = T.ACCENT if self.var.get() else T.BG_INPUT
        target_outline = T.ACCENT if self.var.get() else T.BORDER

        # Draw or clear checkmark
        self.canvas.delete("icon")
        if self.var.get():
            draw_checkmark(self.canvas, 12, 12, 18, T.BG, width=2.5, tag="icon")

        if not animate:
            self.canvas.itemconfigure(self._rect, fill=target_bg, outline=target_outline)
            return

        # Quick color transition
        if self._anim_id:
            self.after_cancel(self._anim_id)

        start_bg = T.BG_INPUT if self.var.get() else T.ACCENT
        steps = 10

        def _step(i):
            if not self.winfo_exists():
                return
            t = ease_in_out(i / steps)
            c = _lerp_color(start_bg, target_bg, t)
            self.canvas.itemconfigure(self._rect, fill=c, outline=c)
            if i < steps:
                self._anim_id = self.after(16, _step, i + 1)

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
        self._fade_out_thumb()

    def _fade_out_thumb(self, step=0, steps=6):
        if not self.winfo_exists():
            return
        if step >= steps:
            self._visible = False
            self.delete("thumb")
            self.lower()
            return
        t = ease_in_out(step / steps)
        fade_color = _lerp_color(self._thumb_color, T.BG, t)
        self.delete("thumb")
        h = self.winfo_height()
        w = self._bar_width
        if h < 20:
            return
        thumb_h = max(30, (self._last - self._first) * h)
        thumb_y = self._first * h
        r = max(2, (w - 2) // 2)
        x1, y1 = 1, max(2, int(thumb_y) + 2)
        x2, y2 = w - 1, min(h - 2, int(thumb_y + thumb_h) - 2)
        round_rect(self, x1, y1, x2, y2, radius=r,
                   fill=fade_color, outline="", tags="thumb")
        self.after(25, self._fade_out_thumb, step + 1, steps)

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
            self._drag_start = (e.y, self._first)
        else:
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



# ---------------------------------------------------------------------------
# Emoji Picker - clickable preset emoji grid (BMP-safe for tkinter)
# ---------------------------------------------------------------------------

class EmojiPicker(tk.Frame):
    """Row of clickable emoji options for break icon selection."""

    PRESETS = ["☕", "⏸", "⏰", "⌛", "☀", "♨", "✦", "♪"]

    def __init__(self, parent, variable=None, bg=None):
        self._bg = bg or parent.cget("bg")
        super().__init__(parent, bg=self._bg)
        self._var = variable or tk.StringVar(value="☕")
        self._buttons = []

        for emoji in self.PRESETS:
            btn = tk.Label(
                self, text=emoji, font=("Segoe UI Emoji", 18),
                bg=self._bg, fg=T.TEXT_MUTED,
                cursor="hand2", padx=6, pady=2,
            )
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, em=emoji: self._select(em))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(
                bg=T.BG_HOVER, fg=T.TEXT))
            btn.bind("<Leave>", lambda e, b=btn: self._style_btn(b))
            self._buttons.append((emoji, btn))

        self._highlight_selected()

    def _select(self, emoji):
        self._var.set(emoji)
        self._highlight_selected()

    def _highlight_selected(self):
        sel = self._var.get()
        for emoji, btn in self._buttons:
            if emoji == sel:
                btn.configure(bg=T.ACCENT_DIM, fg=T.ACCENT)
            else:
                btn.configure(bg=self._bg, fg=T.TEXT_MUTED)

    def _style_btn(self, btn):
        """Restore correct style on leave."""
        sel = self._var.get()
        for emoji, b in self._buttons:
            if b is btn:
                if emoji == sel:
                    btn.configure(bg=T.ACCENT_DIM, fg=T.ACCENT)
                else:
                    btn.configure(bg=self._bg, fg=T.TEXT_MUTED)
                break

    def get(self):
        return self._var.get()

    def set(self, value):
        self._var.set(value)
        self._highlight_selected()


# ---------------------------------------------------------------------------
# Collapsible Section — canvas arrows, smooth expand/collapse
# ---------------------------------------------------------------------------

class CollapsibleSection(tk.Frame):
    """Section with clickable header that toggles content visibility.
    Uses canvas-drawn arrows and smooth expand/collapse animation."""

    def __init__(self, parent, title, count=None, subtitle=None,
                 initially_open=False, bg=None, header_font=None,
                 on_toggle=None):
        self._bg = bg or parent.cget("bg")
        super().__init__(parent, bg=self._bg)
        self._is_open = initially_open
        self._on_toggle = on_toggle
        self._anim_id = None

        self._header = tk.Frame(self, bg=self._bg, cursor="hand2")
        self._header.pack(fill="x", pady=(4, 4))

        # Canvas arrow instead of unicode
        self._arrow_canvas = tk.Canvas(
            self._header, width=16, height=16,
            bg=self._bg, highlightthickness=0, bd=0)
        self._arrow_canvas.pack(side="left", padx=(0, 8), pady=2)
        self._draw_arrow()

        self._title_label = tk.Label(
            self._header, text=title,
            font=header_font or T.FONT_SECTION,
            bg=self._bg, fg=T.TEXT)
        self._title_label.pack(side="left")

        if count is not None:
            self._count_label = tk.Label(
                self._header, text=f"({count})",
                font=T.FONT_MUTED, bg=self._bg, fg=T.ACCENT_MUTED)
            self._count_label.pack(side="left", padx=(6, 0))
        else:
            self._count_label = None

        if subtitle:
            self._subtitle_label = tk.Label(
                self._header, text=subtitle,
                font=T.FONT_MUTED, bg=self._bg, fg=T.TEXT_MUTED)
            self._subtitle_label.pack(side="left", padx=(10, 0))
        else:
            self._subtitle_label = None

        # Content with clip container for animation
        self._clip = tk.Frame(self, bg=self._bg)
        self.content = tk.Frame(self._clip, bg=self._bg)
        self.content.pack(fill="x")

        if initially_open:
            self._clip.pack(fill="x", pady=(T.SPACE_SM, 0))

        # Bind clicks
        click_widgets = [self._header, self._arrow_canvas, self._title_label]
        if self._count_label:
            click_widgets.append(self._count_label)
        if self._subtitle_label:
            click_widgets.append(self._subtitle_label)

        for w in click_widgets:
            w.bind("<Button-1>", self._toggle)

        # Hover feedback
        self._header_widgets = click_widgets
        self._hover_bg = T.BG_SECTION_HOVER

        for w in self._header_widgets:
            w.bind("<Enter>", self._on_header_enter, add="+")
            w.bind("<Leave>", self._on_header_leave, add="+")

    def _draw_arrow(self):
        c = self._arrow_canvas
        c.delete("icon")
        color = T.TEXT_MUTED
        if self._is_open:
            draw_arrow_down(c, 8, 8, 14, color, tag="icon")
        else:
            draw_arrow_right(c, 8, 8, 14, color, tag="icon")

    @property
    def is_open(self):
        return self._is_open

    def _toggle(self, _e=None):
        self._is_open = not self._is_open
        self._draw_arrow()
        if self._is_open:
            self._clip.pack(fill="x", pady=(T.SPACE_SM, 0))
        else:
            self._clip.pack_forget()
        if self._on_toggle:
            self._on_toggle(self._is_open)

    def _on_header_enter(self, _e=None):
        for w in self._header_widgets:
            try:
                w.configure(bg=self._hover_bg)
            except Exception:
                pass

    def _on_header_leave(self, _e=None):
        for w in self._header_widgets:
            try:
                w.configure(bg=self._bg)
            except Exception:
                pass

    def open(self):
        if not self._is_open:
            self._toggle()

    def close(self):
        if self._is_open:
            self._toggle()

    def update_count(self, count):
        if self._count_label:
            self._count_label.configure(text=f"({count})")

    def update_subtitle(self, text):
        if self._subtitle_label:
            self._subtitle_label.configure(text=text)
