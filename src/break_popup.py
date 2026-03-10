"""Break countdown popup — gentle reminder with circular progress ring and rounded card."""
import tkinter as tk

import theme as T
from widgets import RoundedButton, fade_in_window, fade_out_window, draw_circular_progress, round_rect


class BreakPopup:
    def __init__(self, root, on_snooze, on_complete):
        self.root = root
        self.on_snooze = on_snooze
        self.on_complete = on_complete
        self.popup = None
        self._countdown_id = None
        self._remaining = 0
        self._total = 0

    def show(self, duration_seconds, title="Pause", text="Steh auf, streck dich, trink Wasser.", fullscreen=False, icon="\u2615"):
        if self.popup and self.popup.winfo_exists():
            return
        self._remaining = duration_seconds
        self._total = duration_seconds

        self.popup = tk.Toplevel(self.root)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)

        sx = self.popup.winfo_screenwidth()
        sy = self.popup.winfo_screenheight()

        cw, ch = 420, 530
        radius = T.CARD_RADIUS
        margin = 10

        if fullscreen:
            self.popup.geometry(f"{sx}x{sy}+0+0")
            self.popup.configure(bg="#000000", highlightthickness=0)

            card_canvas = tk.Canvas(
                self.popup, width=cw + margin * 2, height=ch + margin * 2,
                bg="#000000", highlightthickness=0, bd=0)
            card_canvas.place(relx=0.5, rely=0.5, anchor="center")
        else:
            pw, ph = cw + margin * 2, ch + margin * 2
            x, y = (sx - pw) // 2, (sy - ph) // 2
            self.popup.geometry(f"{pw}x{ph}+{x}+{y}")
            self.popup.configure(bg="#FF00FF", highlightthickness=0)
            self.popup.attributes("-transparentcolor", "#FF00FF")

            card_canvas = tk.Canvas(
                self.popup, width=pw, height=ph,
                bg="#FF00FF", highlightthickness=0, bd=0)
            card_canvas.pack(fill="both", expand=True)

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
            window=inner, width=cw - 80, height=ch - 56)

        # Icon
        if icon:
            tk.Label(
                inner, text=icon, font=("Segoe UI Emoji", 36),
                bg=T.BG, fg=T.TEXT,
            ).pack(pady=(0, 4))

        # Title
        tk.Label(
            inner, text=title,
            font=(T.FONT, 22, "bold"), bg=T.BG, fg=T.TEXT,
        ).pack(pady=(0, 4))

        # Subtitle
        tk.Label(
            inner, text=text,
            font=(T.FONT, 11), bg=T.BG, fg=T.TEXT_MUTED,
            justify="center",
        ).pack(pady=(0, 16))

        # Circular progress ring with timer text
        ring_size = 200
        self._ring_canvas = tk.Canvas(
            inner, width=ring_size, height=ring_size,
            bg=T.BG, highlightthickness=0, bd=0,
        )
        self._ring_canvas.pack(pady=(0, 16))

        # Snooze button (secondary style)
        RoundedButton(
            inner, text="Schlummern",
            bg=T.BG_INPUT, fg=T.TEXT,
            hover_bg=T.BG_HOVER, hover_fg=T.TEXT,
            command=self._on_snooze,
            width=200, height=48, radius=18,
        ).pack()

        fade_in_window(self.popup, duration_ms=300)
        self._update_countdown()

    def _update_countdown(self):
        if not self.popup or not self.popup.winfo_exists():
            return
        mins, secs = divmod(self._remaining, 60)
        time_text = f"{mins:02d}:{secs:02d}"
        self._draw_ring(time_text)
        if self._remaining > 0:
            self._remaining -= 1
            self._countdown_id = self.root.after(1000, self._update_countdown)
        else:
            self._on_timer_complete()

    def _draw_ring(self, time_text):
        c = self._ring_canvas
        c.delete("all")
        size = 200
        cx, cy = size // 2, size // 2
        radius = 78
        thickness = 10
        fraction = self._remaining / self._total if self._total > 0 else 0

        # Subtle glow layer behind foreground arc
        if fraction > 0.003:
            draw_circular_progress(c, cx, cy, radius, thickness + 6,
                                   fraction, T.ACCENT_DIM)
        draw_circular_progress(c, cx, cy, radius, thickness, fraction, T.ACCENT)

        # Timer text centered in ring
        c.create_text(
            cx, cy, text=time_text,
            font=(T.FONT, T.FONT_SIZE_HERO, "bold"),
            fill=T.TEXT, anchor="center",
        )

    def _on_snooze(self):
        self._fade_and_close(self.on_snooze)

    def _on_timer_complete(self):
        self._fade_and_close(self.on_complete)

    def _fade_and_close(self, callback):
        if self._countdown_id:
            self.root.after_cancel(self._countdown_id)
            self._countdown_id = None
        if self.popup and self.popup.winfo_exists():
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
        if self._countdown_id:
            self.root.after_cancel(self._countdown_id)
            self._countdown_id = None
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        self.popup = None

    @property
    def is_showing(self):
        return self.popup is not None and self.popup.winfo_exists()
