"""Draw the README banner, assets/readme/banner-dark.png and banner-light.png, at 1280x400: the
facet mark, the name and a tagline, in each theme's tokens.

uv run scripts/banner.py

It reuses the share card's mark and fonts (scripts/card.py), so the two stay alike. Edit this
script, not the PNGs.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import card  # noqa: E402
import tokens  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "readme"
W, H, S = 1280, 400, card.SCALE
TAGLINE = "A shared design language for a family of websites."


def draw(theme: int) -> Image.Image:
    """The banner in one theme: 0 is dark, 1 is light. Outside the rounded panel stays clear, so
    the banner sits on GitHub's own background."""
    bg2, fg = tokens.token("bg-2")[theme], tokens.token("fg")[theme]
    accent = tokens.token("accent")[theme]
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(
        (0, 0, W * S - 1, H * S - 1),
        radius=36 * S,
        fill=bg2,
        outline=card.mix(bg2, fg, 0.12),
        width=2 * S,
    )

    cx, cy, size = 236 * S, 186 * S, 128 * S
    for points, t in card.GEM:
        poly = [(cx + px * size, cy + py * size) for px, py in points]
        d.polygon(poly, fill=card.mix(bg2, accent, t), outline=card.mix(bg2, fg, 0.35), width=S)

    x = 440 * S
    serif = card.font("source-serif-4", 136, weight=600, optical_size=60)
    d.text((x - 5 * S, 58 * S), "facet", font=serif, fill=fg)
    sans = card.font("geist", 30, weight=400)
    d.text((x, 236 * S), TAGLINE, font=sans, fill=card.mix(bg2, fg, 0.72))

    r, gap, y = 10 * S, 32 * S, 316 * S
    for i, pair in enumerate(tokens.accents().values()):
        dx = x + r + i * gap
        d.ellipse((dx - r, y - r, dx + r, y + r), fill=pair[theme])

    return img.resize((W, H), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for theme, name in enumerate(["dark", "light"]):
        path = OUT / f"banner-{name}.png"
        # Full color: a 256-color palette merges the near-neutral accent dots into one gray.
        draw(theme).save(path, optimize=True)
        print(f"wrote {path.relative_to(ROOT)}")
