"""Read facet's color tokens from src/css as sRGB, for the tooling that cannot run CSS (the share
card, theme-color). The CSS stays the single source of truth."""

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "src" / "css"
COLOR = r"oklch\(([\d.]+) ([\d.]+) ([\d.]+)\)|#([0-9a-f]{6})\b"


def oklch_to_rgb(lightness: float, chroma: float, hue: float) -> tuple[int, int, int]:
    """Convert OKLCH to 8-bit sRGB, clamped to the gamut."""
    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))
    lms = [
        (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3,
        (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3,
        (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3,
    ]
    linear = [
        4.0767416621 * lms[0] - 3.3077115913 * lms[1] + 0.2309699292 * lms[2],
        -1.2684380046 * lms[0] + 2.6097574011 * lms[1] - 0.3413193965 * lms[2],
        -0.0041960863 * lms[0] - 0.7034186147 * lms[1] + 1.7076147010 * lms[2],
    ]

    def encode(x: float) -> int:
        x = min(max(x, 0.0), 1.0)
        x = 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
        return round(x * 255)

    return tuple(encode(x) for x in linear)


def _rgb(match: tuple[str, ...]) -> tuple[int, int, int]:
    *lch, hexa = match
    if hexa:
        return tuple(int(hexa[i : i + 2], 16) for i in (0, 2, 4))
    return oklch_to_rgb(*map(float, lch))


def _pair(text: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """The (dark, light) colors of one `var(--f-unless-light, …) var(--f-unless-dark, …)` value."""
    dark, light = (_rgb(m) for m in re.findall(COLOR, text)[:2])
    return dark, light


def token(name: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """The (dark, light) sRGB values of a color token in 10-tokens.css, e.g. token("bg")."""
    css = (CSS / "10-tokens.css").read_text()
    match = re.search(rf"--f-{name}:(.*?);", css, re.S)
    return _pair(match.group(1))


def accents() -> dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]]:
    """Every accent preset in 20-accents.css, in file order, as (dark, light) sRGB."""
    css = (CSS / "20-accents.css").read_text()
    out = {}
    for name, body in re.findall(r'\[data-accent="([a-z]+)"\]\s*\{(.*?)\}', css, re.S):
        out[name] = _pair(re.search(r"--f-accent:(.*?);", body, re.S).group(1))
    return out


def hex_color(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)
