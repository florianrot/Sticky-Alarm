"""Design tokens — Apple-like dark theme."""

# === Colors ===
BG = "#0f0f0f"
BG_CARD = "#161616"
BG_INPUT = "#1c1c1c"
BG_HOVER = "#262626"
BORDER = "#2a2a2a"
BORDER_FOCUS = "#444444"

TEXT = "#f5f5f5"
TEXT_SECONDARY = "#b0b0b0"
TEXT_MUTED = "#909090"          # brighter than before
LABEL = "#a0a0a0"              # section labels — clearly visible

ACCENT = "#ffffff"
DANGER = "#ff4466"
DANGER_DIM = "#1f0a10"
SUCCESS = "#4ade80"

# === Typography ===
FONT = "Segoe UI"
FONT_SIZE_XS = 9
FONT_SIZE_SM = 10
FONT_SIZE_BASE = 11
FONT_SIZE_LG = 13
FONT_SIZE_XL = 16
FONT_SIZE_2XL = 20
FONT_SIZE_HERO = 32

# === Font tuples ===
FONT_LABEL = (FONT, FONT_SIZE_SM, "bold")
FONT_BODY = (FONT, FONT_SIZE_BASE)
FONT_BODY_LG = (FONT, FONT_SIZE_LG)
FONT_BUTTON = (FONT, FONT_SIZE_BASE, "bold")
FONT_BUTTON_LG = (FONT, FONT_SIZE_LG, "bold")
FONT_HEADING = (FONT, FONT_SIZE_XL, "bold")
FONT_HERO = (FONT, FONT_SIZE_HERO, "bold")
FONT_INPUT = (FONT, FONT_SIZE_LG)
FONT_MUTED = (FONT, FONT_SIZE_SM)

# === Animation speeds (ms) ===
ANIM_FAST = 150
ANIM_NORMAL = 300
ANIM_SLOW = 500
