"""Take the README's screenshots of the reference site into assets/readme/ as WebP.

uv run scripts/shots.py   (or `just shots`, which builds dist/ first)

Each shot loads a page of site/ in Chromium with reduced motion (so videos and typing hold still)
and hides the reference site's toolbar, so it shows a page as a facet site would look. Pages
render at 2x and are saved at most 1600px wide, sharp on high-density screens yet small.
"""

import functools
import http.server
import io
import threading
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUT = ROOT / "assets" / "readme"
W, H = 1280, 720

HIDE_BAR = ".site-bar { display: none !important; }"

# The components page is one long column; this lays a few sections side by side and hides the
# rest, the Markup blocks and the prose between them.
BOARD = """
main > header, main > section, details.site-markup, .f-footer,
main .f-kicker:first-child, main > section > p:not([class]) { display: none !important; }
main {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  grid-template-rows: repeat(4, auto) 1fr !important;
  gap: 28px 48px !important;
  width: auto !important;
  max-width: none !important;
  margin: 0 !important;
  padding: 40px 48px !important;
}
main > section:is(:nth-of-type(-n + 4), :nth-of-type(6), #hero) {
  display: block !important;
  margin: 0 !important;
  padding: 0 !important;
}
main > section:nth-of-type(-n + 4) { grid-column: 1; }
main > section#hero { grid-area: 1 / 2 / 6 / 3; }
main > section:nth-of-type(6) { grid-area: 1 / 3 / 6 / 4; }
main > section > h2 { margin: 0 0 12px !important; }
"""


class Shooter:
    def __init__(self, browser, base: str):
        self.browser, self.base = browser, base

    def shot(self, path, theme, *, css="", clip=None, selector=None, pad=0, height=H):
        ctx = self.browser.new_context(
            viewport={"width": W, "height": height}, reduced_motion="reduce", device_scale_factor=2
        )
        page = ctx.new_page()
        page.goto(f"{self.base}/{path}?theme={theme}&lang=en&accent=")
        page.add_style_tag(content=HIDE_BAR + css)
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(300)
        if selector:
            box = page.locator(selector).bounding_box()
            clip = {
                "x": max(0, box["x"] - pad),
                "y": max(0, box["y"] - pad),
                "width": min(W, box["width"] + 2 * pad),
                "height": box["height"] + 2 * pad,
            }
        png = page.screenshot(clip=clip, full_page=clip is not None)
        ctx.close()
        return Image.open(io.BytesIO(png)).convert("RGB")


def split(dark: Image.Image, light: Image.Image) -> Image.Image:
    """The dark shot's left half next to the light shot's right half, with a hairline seam."""
    out = dark.copy()
    half = out.width // 2
    out.paste(light.crop((half, 0, light.width, light.height)), (half, 0))
    ImageDraw.Draw(out).line((half, 0, half, out.height), fill=(128, 134, 145), width=2)
    return out


def save(img: Image.Image, name: str, width: int = 1600):
    if img.width > width:
        img = img.resize((width, round(img.height * width / img.width)), Image.Resampling.LANCZOS)
    path = OUT / f"{name}.webp"
    img.save(path, "WEBP", quality=82, method=6)
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)")


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        s = Shooter(browser, f"http://127.0.0.1:{server.server_port}")
        save(s.shot("layouts/landing.html", "dark"), "landing")
        save(s.shot("layouts/docs.html", "light"), "docs")
        board = {"x": 0, "y": 0, "width": W, "height": 580}
        save(s.shot("components.html", "dark", css=BOARD, clip=board), "components")
        save(
            s.shot(
                "cast.html", "light", css=".f-footer { display: none; }", selector="#cast", pad=24
            ),
            "cast",
        )
        dark, light = (s.shot("layouts/resume.html", theme) for theme in ("dark", "light"))
        save(split(dark, light), "themes")
        browser.close()
    server.shutdown()


if __name__ == "__main__":
    main()
