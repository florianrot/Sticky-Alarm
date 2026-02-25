"""Generate .ico file for Sticky Alarm — white alarm clock on dark background."""

from PIL import Image, ImageDraw


def draw_alarm(draw, size, fg="#ffffff", hand="#1a1a1a"):
    """Draw alarm clock silhouette at given size (designed for 64-unit grid)."""
    s = size / 64
    # Clock body
    draw.ellipse([int(8*s), int(12*s), int(56*s), int(60*s)], fill=fg)
    # Bell top
    draw.polygon([
        (int(22*s), int(14*s)),
        (int(32*s), int(4*s)),
        (int(42*s), int(14*s))
    ], fill=fg)
    # Hour hand
    cx, cy = int(32*s), int(36*s)
    draw.line([cx, cy, cx, int(22*s)], fill=hand, width=max(2, int(3*s)))
    # Minute hand
    draw.line([cx, cy, int(42*s), cy], fill=hand, width=max(1, int(2*s)))


def create_ico(path="icon.ico"):
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Dark rounded background
    s = size / 64
    r = int(10 * s)
    draw.rounded_rectangle(
        [int(2*s), int(2*s), size - int(2*s), size - int(2*s)],
        radius=r, fill="#1a1a1a"
    )
    draw_alarm(draw, size)
    img.save(path, format="ICO",
             sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Created {path}")


if __name__ == "__main__":
    create_ico()
