"""In-page checks shared by the browser tests."""

# Composites the color over an opaque backdrop so translucent colors resolve to what is seen.
TO_RGB = """
(c, backdrop) => { const x = document.createElement('canvas').getContext('2d');
  x.fillStyle = backdrop || '#000'; x.fillRect(0, 0, 1, 1);
  x.fillStyle = c; x.fillRect(0, 0, 1, 1);
  const d = x.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2]]; }
"""


def no_hscroll(page):
    sw, iw = page.evaluate("[document.documentElement.scrollWidth, innerWidth]")
    assert sw <= iw, f"horizontal scroll: {sw} > {iw}"


def _lum(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (ch(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(page, selector, bg_selector="body"):
    """Contrast of an element's text against bg_selector's background (over the body's)."""
    bg = page.evaluate(
        f"""(() => {{
          const f = ({TO_RGB});
          const base = f(getComputedStyle(document.body).backgroundColor);
          const own = getComputedStyle(document.querySelector({bg_selector!r})).backgroundColor;
          return f(own, `rgb(${{base.join(' ')}})`);
        }})()"""
    )
    fg = page.evaluate(
        f"([sel, bg]) => ({TO_RGB})(getComputedStyle(document.querySelector(sel)).color,"
        " `rgb(${bg.join(' ')})`)",
        [selector, bg],
    )
    a, b = sorted([_lum(fg), _lum(bg)], reverse=True)
    return (a + 0.05) / (b + 0.05)


def contrast_on(page, selector):
    """Contrast of an element's text against its own background (body's if it is transparent)."""
    fg, bg = page.evaluate(
        f"""(() => {{
          const el = document.querySelector({selector!r});
          const f = ({TO_RGB});
          const own = getComputedStyle(el).backgroundColor;
          const base = f(getComputedStyle(document.body).backgroundColor);
          const bg = f(own, `rgb(${{base.join(' ')}})`);
          return [f(getComputedStyle(el).color, `rgb(${{bg.join(' ')}})`), bg];
        }})()"""
    )
    a, b = sorted([_lum(fg), _lum(bg)], reverse=True)
    return (a + 0.05) / (b + 0.05)


def running_animations(page):
    return page.evaluate("document.getAnimations().filter(a => a.playState === 'running').length")


def cat_text_overlaps(page):
    return page.evaluate("""() => {
      const cats = [...document.querySelectorAll('.cat')].map(c => c.getBoundingClientRect());
      if (!cats.length) return 0;
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let hits = 0, n;
      while ((n = walker.nextNode())) {
        if (!n.textContent.trim()) continue;
        if (n.parentElement.closest('[aria-hidden="true"], .cat')) continue;
        const r = document.createRange(); r.selectNodeContents(n);
        for (const t of r.getClientRects()) for (const c of cats)
          if (t.left < c.right && t.right > c.left && t.top < c.bottom && t.bottom > c.top) hits++;
      }
      return hits;
    }""")


def focus_ring(page, selector):
    page.focus(selector)
    return page.evaluate(
        f"(() => {{ const s = getComputedStyle(document.querySelector({selector!r}));"
        " return s.outlineStyle + ' ' + s.outlineWidth; })()"
    )
