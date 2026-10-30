"""Draw the portrait promo poster, assets/poster.png, at 1440x2400: the facet mark and name, a
hero card, the cast sitting on a glass panel, and QR codes to the repository and the docs.

uv run --with segno scripts/poster.py   (or `just poster`, which builds dist/ first)

The page is built from facet itself (dist/facet.css, the cast, the fonts) in the dark theme and
taken in Chromium with reduced motion, so the cats hold their poses. Edit this script, not the PNG.
"""

import functools
import http.server
import sys
import threading
from pathlib import Path

import segno
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
import tokens  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "poster.png"
W, H = 1440, 2400
REPO = "https://github.com/h1994st/facet"
DOCS = "https://shengtuo.me/facet/"

# The facet mark (scripts/card.py GEM): each facet and how far its fill leans to the accent.
GEM = [
    ("-1,0 -0.55,-0.6 -0.35,0", 55),
    ("-0.55,-0.6 0.55,-0.6 0.35,0 -0.35,0", 85),
    ("0.55,-0.6 1,0 0.35,0", 40),
    ("-1,0 -0.35,0 0,1", 35),
    ("-0.35,0 0.35,0 0,1", 60),
    ("0.35,0 1,0 0,1", 22),
]
GITHUB = (ROOT / "dist" / "icons" / "github.svg").read_text()


def gem(cls: str) -> str:
    faces = "".join(
        f'<polygon points="{p}" style="fill: color-mix(in oklch, var(--f-bg-2), var(--f-accent) '
        f'{t}%)"/>'
        for p, t in GEM
    )
    return (
        f'<svg class="{cls}" viewBox="-1.05 -0.65 2.1 1.7" aria-hidden="true">'
        f'<g stroke-width="0.012" stroke-linejoin="round">{faces}</g></svg>'
    )


def qr(url: str, logo: str) -> str:
    """A QR code as SVG with a logo in a cleared center (error correction H leaves room for it).
    The modules stay square: rounded finder patterns trip some decoders."""
    code = segno.make(url, error="h", boost_error=False)
    rows = [list(r) for r in code.matrix]
    n = len(rows)
    hole = round(n * 0.26) | 1  # an odd number of modules, so it centers
    lo = (n - hole) // 2
    path = "".join(
        f"M{c} {r}h1v1h-1z"
        for r in range(n)
        for c in range(n)
        if rows[r][c] and not (lo - 1 <= r <= lo + hole and lo - 1 <= c <= lo + hole)
    )
    return (
        f'<svg class="qr" viewBox="0 0 {n} {n}" role="img" aria-label="{url}">'
        f'<path d="{path}"/>'
        f'<svg x="{lo}" y="{lo}" width="{hole}" height="{hole}">{logo}</svg></svg>'
    )


def logo_github() -> str:
    return GITHUB.replace("<svg ", '<svg width="100%" height="100%" ')


def logo_gem() -> str:
    faces = "".join(
        f'<polygon points="{p}" style="fill: color-mix(in oklch, #fff, var(--f-accent-deep) '
        f'{55 + t * 0.5:.0f}%)"/>'
        for p, t in GEM
    )
    return (
        f'<svg width="100%" height="100%" viewBox="-1.1 -0.75 2.2 1.9">'
        f'<g stroke-width="0.03" stroke-linejoin="round">{faces}</g></svg>'
    )


CSS = """
html, body { margin: 0; width: 1440px; height: 2400px; overflow: hidden; }
body {
  /* Soft glows in the accent and two muted neighbors (sage, iris), as on facet's own pages. */
  --glow-top: color-mix(in oklch, var(--f-accent) 20%, transparent);
  --glow-left: color-mix(in oklch, oklch(0.76 0.06 130) 9%, transparent);
  --glow-right: color-mix(in oklch, oklch(0.76 0.06 300) 11%, transparent);
  background:
    radial-gradient(900px 700px at 50% 4%, var(--glow-top), transparent 70%),
    radial-gradient(900px 800px at 6% 62%, var(--glow-left), transparent 70%),
    radial-gradient(1000px 900px at 100% 92%, var(--glow-right), transparent 70%),
    var(--f-bg);
  color: var(--f-fg);
  font-family: var(--f-font-sans);
}
.poster {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  padding: 120px 120px 100px;
}
.mark { width: 230px; filter: drop-shadow(0 30px 50px rgb(0 0 0 / 0.45)); }
.mark polygon { stroke: color-mix(in oklch, var(--f-bg-2), var(--f-fg) 35%); }
h1 {
  margin: 30px 0 0;
  font: 600 250px / 0.9 var(--f-font-serif);
  font-variation-settings: "opsz" 60;
  letter-spacing: -0.035em;
}
.tagline {
  margin: 36px 0 0;
  color: var(--f-fg-2);
  font: 400 46px / 1.3 var(--f-font-sans);
  text-align: center;
}
.dots { display: flex; gap: 20px; margin-top: 48px; }
.dots i { width: 30px; height: 30px; border-radius: 50%; }

.f-hero {
  box-sizing: border-box;
  width: 100%;
  margin-top: 84px;
  padding: 64px 72px;
  box-shadow: var(--f-shadow-hi);
}
.f-hero__kicker { font-size: 22px; margin-bottom: 30px; }
.f-hero__title { max-inline-size: none; font-size: 100px; margin-bottom: 32px; }
.f-hero__lead { max-inline-size: 30ch; margin: 0; font-size: 36px; opacity: 0.86; }
.chips { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 42px; }
.chips .f-chip {
  padding: 8px 22px;
  background: color-mix(in oklch, var(--f-on-accent-deep) 14%, transparent);
  color: var(--f-on-accent-deep);
  font-size: 25px;
}

.stage { position: relative; width: 100%; margin-top: auto; }
/* The cast sits on the panel's top edge, like the footer cats. */
.cats { position: absolute; right: 80px; bottom: calc(100% - 22px); display: flex; gap: 6px; }
.cats .cat { width: 190px; }
.panel {
  box-sizing: border-box;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 56px;
  width: 100%;
  padding: 60px 70px 54px;
  border: 1px solid var(--f-glass-edge);
  border-radius: 44px;
  background: var(--f-glass-bg);
  -webkit-backdrop-filter: blur(var(--f-glass-blur)) saturate(140%);
  backdrop-filter: blur(var(--f-glass-blur)) saturate(140%);
  box-shadow: var(--f-shadow-hi);
}
.code { display: flex; flex-direction: column; align-items: center; text-align: center; }
.tile {
  padding: 40px;
  border-radius: 32px;
  background: oklch(0.96 0.008 260);
  color: oklch(0.2 0.012 260);
  box-shadow: 0 0 0 1px rgb(255 255 255 / 0.14), var(--f-shadow);
}
.qr { display: block; width: 330px; height: 330px; fill: currentColor; }
.code .f-kicker {
  margin: 30px 0 8px;
  color: var(--f-fg-3);
  font: 500 22px / 1.2 var(--f-font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.code b { font: 600 34px / 1.3 var(--f-font-sans); letter-spacing: -0.01em; }
"""


def page() -> str:
    # Every accent's dark value, in the order of src/css/20-accents.css.
    dots = "".join(
        '<i style="background: rgb({} {} {})"></i>'.format(*pair[0])
        for pair in tokens.accents().values()
    )
    chips = "".join(
        f'<span class="f-chip">{c}</span>'
        for c in ["Design tokens", "Components", "15 layouts", "Dark &amp; light", "English · 中文"]
    )
    return f"""<!doctype html>
<html lang="en" data-theme="dark" data-accent="slate">
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="/dist/facet.css">
<link rel="stylesheet" href="/dist/cast/cast-layered.css">
<style>{CSS}</style>
</head>
<body>
<main class="poster">
  {gem("mark")}
  <h1>facet</h1>
  <p class="tagline">A shared design language<br>for a family of websites.</p>
  <div class="dots">{dots}</div>

  <section class="f-hero">
    <div>
      <p class="f-hero__kicker">Plain CSS · vanilla JS · no build step</p>
      <h2 class="f-hero__title">Cut from the same glass.</h2>
      <p class="f-hero__lead">Each site picks its own accent and shares everything else.</p>
      <div class="chips">{chips}</div>
    </div>
  </section>

  <div class="stage">
    <div class="cats" id="cats"></div>
    <section class="panel">
      <div class="code">
        <div class="tile">{qr(REPO, logo_github())}</div>
        <p class="f-kicker">Source</p>
        <b>github.com/h1994st/facet</b>
      </div>
      <div class="code">
        <div class="tile">{qr(DOCS, logo_gem())}</div>
        <p class="f-kicker">Docs &amp; live examples</p>
        <b>shengtuo.me/facet</b>
      </div>
    </section>
  </div>
</main>
<script type="module">
  import {{ createCat }} from "/dist/cast/cast.js";
  document.getElementById("cats").append(
    createCat("dudu", {{ pose: "blink", label: "" }}),
    createCat("nangnang", {{ label: "" }}),
    createCat("duna", {{ pose: "wave", label: "" }}),
  );
  document.body.dataset.ready = "1";
</script>
</body>
</html>"""


def main():
    html = page()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": W, "height": H}, reduced_motion="reduce", device_scale_factor=1
        )
        pg = ctx.new_page()
        pg.route(
            f"{base}/poster.html", lambda route: route.fulfill(body=html, content_type="text/html")
        )
        pg.goto(f"{base}/poster.html")
        pg.wait_for_selector("body[data-ready]")
        pg.evaluate("document.fonts.ready.then(() => true)")
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT))
        browser.close()
    server.shutdown()
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
