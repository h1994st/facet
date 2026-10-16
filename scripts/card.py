"""Draw the reference site's share card (og:image), site/card.png, at 1200x630, and its icon,
site/favicon.svg, from the same facet mark.

uv run scripts/card.py

Colors come from src/css (scripts/tokens.py) and type from dist/fonts, so the card follows the
tokens. Edit this script, not the PNG; the output is deterministic for a given Pillow.
"""

import io
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import tokens  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "card.png"
ICON = ROOT / "site" / "favicon.svg"
W, H, SCALE = 1200, 630, 2  # drawn at 2x, then downsampled for smooth edges


def font(name: str, size: int, **axes: int) -> ImageFont.FreeTypeFont:
    """A WOFF2 from dist/fonts, decompressed in memory, at the given variation axes."""
    tt = TTFont(ROOT / "dist" / "fonts" / f"{name}.woff2")
    tt.flavor = None
    buf = io.BytesIO()
    tt.save(buf)
    buf.seek(0)
    f = ImageFont.truetype(buf, size * SCALE)
    if axes:
        values = []
        for axis in f.get_variation_axes():
            name = axis["name"].decode().lower().replace(" ", "_")
            values.append(axes.get(name, axis["default"]))
        f.set_variation_by_axes(values)
    return f


# The facet mark: a cut gem, in unit coordinates (x right, y down). Each facet is a polygon and
# the lightness of its fill; site/favicon.svg draws the same shape.
GEM = [
    ([(-1, 0), (-0.55, -0.6), (-0.35, 0)], 0.55),
    ([(-0.55, -0.6), (0.55, -0.6), (0.35, 0), (-0.35, 0)], 0.85),
    ([(0.55, -0.6), (1, 0), (0.35, 0)], 0.4),
    ([(-1, 0), (-0.35, 0), (0, 1)], 0.35),
    ([(-0.35, 0), (0.35, 0), (0, 1)], 0.6),
    ([(0.35, 0), (1, 0), (0, 1)], 0.22),
]


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))


def draw() -> Image.Image:
    bg, bg2, fg = tokens.token("bg")[0], tokens.token("bg-2")[0], tokens.token("fg")[0]
    accents = [dark for dark, _ in tokens.accents().values()]
    s = SCALE
    img = Image.new("RGB", (W * s, H * s), bg)
    d = ImageDraw.Draw(img)

    # A glass panel, as on facet's floating chrome: a lighter surface and a hairline edge.
    pad = 56 * s
    d.rounded_rectangle(
        (pad, pad, W * s - pad, H * s - pad),
        radius=40 * s,
        fill=bg2,
        outline=mix(bg2, fg, 0.1),
        width=2 * s,
    )

    accent = tokens.token("accent")[0]
    cx, cy, size = 905 * s, 250 * s, 150 * s
    for points, t in GEM:
        poly = [(cx + px * size, cy + py * size) for px, py in points]
        d.polygon(poly, fill=mix(bg2, accent, t), outline=mix(bg2, fg, 0.35), width=s)

    x = 120 * s
    serif = font("source-serif-4", 168, weight=600, optical_size=60)
    d.text((x - 6 * s, 132 * s), "facet", font=serif, fill=fg)

    sans = font("geist", 38, weight=400)
    for i, line in enumerate(
        ["A shared design language for a family of", "websites, in plain CSS and small JS."]
    ):
        d.text((x, 360 * s + i * 54 * s), line, font=sans, fill=mix(bg2, fg, 0.72))

    # The thirteen accents, one dot each.
    r, gap, y = 13 * s, 40 * s, 512 * s
    for i, color in enumerate(accents):
        cx = x + r + i * gap
        d.ellipse((cx - r, y - r, cx + r, y + r), fill=color)

    mono = font("geist-mono", 26, weight=400)
    label = "shengtuo.me/facet"
    width = d.textlength(label, font=mono)
    d.text((W * s - 120 * s - width, y - 17 * s), label, font=mono, fill=mix(bg2, fg, 0.5))

    return img.resize((W, H), Image.Resampling.LANCZOS)


def icon() -> str:
    """The facet mark as an SVG icon, lightened so it reads on dark and light browser chrome."""
    bg, accent = tokens.token("bg")[0], tokens.token("accent")[0]
    polys = "".join(
        f'<polygon points="{" ".join(f"{x},{y}" for x, y in points)}" '
        f'fill="{tokens.hex_color(mix(bg, accent, 0.35 + 0.65 * t))}"/>'
        for points, t in GEM
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1.05 -0.85 2.1 2.1">'
        f'<g stroke="{tokens.hex_color(bg)}" stroke-width="0.03" stroke-linejoin="round">'
        f"{polys}</g>"
        "</svg>\n"
    )


if __name__ == "__main__":
    draw().save(OUT, optimize=True)
    ICON.write_text(icon())
    print(f"wrote {OUT.relative_to(ROOT)} and {ICON.relative_to(ROOT)}")
