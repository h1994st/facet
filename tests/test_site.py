from pathlib import Path

import pytest
from checks import TO_RGB, _lum, cat_text_overlaps, contrast, contrast_on, no_hscroll

SITE = Path(__file__).resolve().parents[1] / "site"
# Every reference-site page except the test fixtures; the symlinked dist/ and assets/ are skipped.
PAGES = sorted(
    p.relative_to(SITE).as_posix()
    for p in SITE.rglob("*.html")
    if p.relative_to(SITE).parts[0] not in ("tests", "dist", "assets")
)


# Toolbar links; on any other page no link is current, and every layouts/* page marks "Layouts".
LINKED = {
    "index.html",
    "tokens.html",
    "color.html",
    "type.html",
    "components.html",
    "cast.html",
    "seo.html",
}


def settle(page):
    """Wait for web fonts, so the layout measured is the final one."""
    page.evaluate("document.fonts.ready.then(() => true)")


def pick(page, key, value):
    """Press a toolbar button. Full-screen layouts (deck, panels) scroll the toolbar out of reach,
    so this clicks it in the page rather than with the mouse."""
    page.evaluate(
        '([k, v]) => document.querySelector(`.site-bar button[data-k="${k}"][data-v="${v}"]`)'
        ".click()",
        [key, value],
    )


@pytest.mark.parametrize("path", PAGES)
def test_page(page_factory, site_url, path):
    """Every page, loaded once: the toolbar, then each language x theme x width switched in place
    (the toolbar swaps theme and language without a reload): no sideways scroll, cats clear of
    text, and open Markup blocks that scroll inside themselves."""
    page = page_factory(width=1280)
    page.goto(f"{site_url}/{path}")
    settle(page)

    assert page.locator("header.site-bar").count() == 1
    assert page.locator(".site-bar .site-dot").count() == len(ACCENTS)
    current = page.locator('.site-bar a[aria-current="page"]')
    expected = 1 if path in LINKED or path.startswith("layouts/") else 0
    assert current.count() == expected, path
    if path.startswith("layouts/"):
        assert current.inner_text() == "Layouts"

    for lang in ("en", "zh"):
        pick(page, "lang", lang)
        for theme in ("dark", "light"):
            pick(page, "theme", theme)
            for width in (390, 860, 1280):
                page.set_viewport_size({"width": width, "height": 900})
                settle(page)
                where = f"{path} {lang} {theme} {width}px"
                sw, iw = page.evaluate("[document.documentElement.scrollWidth, innerWidth]")
                assert sw <= iw, f"horizontal scroll on {where}: {sw} > {iw}"
                assert cat_text_overlaps(page) == 0, f"a cat covers text on {where}"

    if path in MARKUP_PAGES:
        page.evaluate("document.querySelectorAll('details.site-markup').forEach(d => d.open = 1)")
        for width in (390, 1280):
            page.set_viewport_size({"width": width, "height": 900})
            settle(page)
            no_hscroll(page)
            assert cat_text_overlaps(page) == 0, f"{path} {width}px with Markup open"
            # Nor widen a container that clips (a full-screen panel or deck stage hides overflow).
            for sel in ["details.site-markup", "main h2"]:
                right = page.evaluate(
                    f"Math.max(0, ...[...document.querySelectorAll({sel!r})]"
                    ".filter(e => e.checkVisibility()).map(e => e.getBoundingClientRect().right))"
                )
                assert right <= width, (path, width, sel)
        # Long lines scroll inside the code block.
        for overflow in page.evaluate(
            "[...document.querySelectorAll('details.site-markup pre')]"
            ".map(p => getComputedStyle(p).overflowX)"
        ):
            assert overflow == "auto", path

    assert page.errors == [], path


ACCENTS = [
    "rose",
    "clay",
    "ochre",
    "moss",
    "sage",
    "teal",
    "slate",
    "lavender",
    "stone",
    "lichen",
    "steel",
    "heather",
    "graphite",
]


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_every_accent_is_readable(page_factory, site_url, theme):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}/color.html")
    for accent in ACCENTS:
        pick(page, "accent", accent)
        assert page.evaluate("document.documentElement.dataset.accent") == accent
        assert contrast_on(page, ".f-btn--primary") >= 4.5, accent
        assert contrast(page, "main a") >= 4.5, accent


def test_toolbar_sets_and_saves_choices(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/index.html")
    page.click('.site-bar button[data-k="theme"][data-v="light"]')
    page.click('.site-bar button[data-k="lang"][data-v="zh"]')
    page.click('.site-bar button[data-v="rose"]')
    root = "document.documentElement"
    assert page.evaluate(f"[{root}.dataset.theme, {root}.lang, {root}.dataset.accent]") == [
        "light",
        "zh-Hans",
        "rose",
    ]
    saved = page.evaluate("JSON.parse(localStorage.getItem('facet-site'))")
    assert saved == {"theme": "light", "lang": "zh", "accent": "rose"}
    assert page.evaluate("localStorage.getItem('facet-theme')") == "light"


def test_url_parameters_override_and_swap_text(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/color.html?lang=zh&accent=teal&theme=light")
    root = "document.documentElement"
    assert page.evaluate(f"[{root}.dataset.theme, {root}.lang, {root}.dataset.accent]") == [
        "light",
        "zh-Hans",
        "teal",
    ]
    assert page.locator("h1").inner_text() == "色彩"


def test_saved_theme_applies_before_first_paint(page_factory, site_url):
    page = page_factory(theme="light")
    page.add_init_script("localStorage.setItem('facet-theme', 'auto')")
    # Record the theme at the moment <body> is first inserted: only a script that ran
    # synchronously in <head> can have set it by then (not a deferred or end-of-body one).
    page.add_init_script(
        "new MutationObserver((_, obs) => { if (document.body) {"
        " window.__atBody = document.documentElement.dataset.theme; obs.disconnect() } })"
        ".observe(document, { childList: true, subtree: true })"
    )
    page.goto(f"{site_url}/index.html")
    # facet-theme wins over facet-site.theme.
    assert page.evaluate("window.__atBody") == "auto"


def test_bogus_choices_are_ignored(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/index.html?theme=bogus&accent=zzz&lang=xx")
    root = "document.documentElement"
    assert page.evaluate(f"[{root}.dataset.theme, {root}.lang, {root}.dataset.accent]") == [
        "dark",
        "en",
        None,
    ]
    stored = page.evaluate(
        "[localStorage.getItem('facet-site'), localStorage.getItem('facet-theme')].join('|')"
    )
    assert "bogus" not in stored and "zzz" not in stored and "xx" not in stored.replace("xxx", "")


def test_bogus_saved_values_are_ignored(page_factory, site_url):
    page = page_factory()
    page.add_init_script(
        "localStorage.setItem('facet-site', JSON.stringify({theme:'x', lang:'y', accent:'z'}));"
        "localStorage.setItem('facet-theme', 'nope')"
    )
    page.goto(f"{site_url}/index.html")
    root = "document.documentElement"
    assert page.evaluate(f"[{root}.dataset.theme, {root}.lang, {root}.dataset.accent]") == [
        "auto",
        "en",
        None,
    ]


def test_reference_site_defaults_to_auto(browser, site_url):
    ctx = browser.new_context(color_scheme="light")
    try:
        page = ctx.new_page()
        page.goto(f"{site_url}/components.html")
        assert page.evaluate("document.documentElement.dataset.theme") == "auto"
        assert page.get_attribute(
            '.site-bar button[data-k="theme"][data-v="auto"]', "aria-pressed"
        ) == ("true")
    finally:
        ctx.close()


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_no_data_theme_follows_the_system(browser, site_url, scheme):
    bg = {"dark": "oklch(0.2 0.012 260)", "light": "oklch(0.975 0.004 260)"}
    ctx = browser.new_context(color_scheme=scheme)
    try:
        page = ctx.new_page()
        page.goto(f"{site_url}/tests/no-theme.html")
        assert page.evaluate("document.documentElement.dataset.theme") is None
        body = "getComputedStyle(document.body).backgroundColor"
        assert page.evaluate(body) == bg[scheme]
        # An explicit theme still wins over the system, and print stays light.
        for forced in ("dark", "light"):
            page.evaluate(f"document.documentElement.dataset.theme = {forced!r}")
            assert page.evaluate(body) == bg[forced]
        page.evaluate("delete document.documentElement.dataset.theme")
        page.emulate_media(media="print")
        assert page.evaluate(body) == bg["light"]
    finally:
        ctx.close()


def test_auto_theme_shows_pressed(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/index.html?theme=auto")
    assert page.get_attribute(
        '.site-bar button[data-k="theme"][data-v="auto"]', "aria-pressed"
    ) == ("true")


@pytest.mark.parametrize("scheme", ["dark", "light"])
@pytest.mark.parametrize("theme", ["dark", "light", "auto"])
def test_color_tile_button_text_is_readable(browser, site_url, theme, scheme):
    ctx = browser.new_context(color_scheme=scheme)
    try:
        page = ctx.new_page()
        page.goto(f"{site_url}/color.html?theme={theme}")
        for hue in ACCENTS:
            sel = f'.site-tile[data-hue="{hue}"] .site-tile__btn'
            assert contrast_on(page, sel) >= 4.5, (hue, theme, scheme)
    finally:
        ctx.close()


def test_app_layout_fills_the_window_below_the_bar(page_factory, site_url):
    page = page_factory(width=1280)
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(f"{site_url}/layouts/app.html")
    page.wait_for_timeout(200)
    # The fixed app cannot scroll the bar away, so it must start below the bar and never
    # let the body scroll.
    assert page.evaluate("document.scrollingElement.scrollHeight <= innerHeight + 1")
    bar = page.evaluate("document.querySelector('.site-bar').getBoundingClientRect().bottom")
    top = page.evaluate("document.querySelector('.f-app').getBoundingClientRect().top")
    assert top >= bar - 1


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_status_alerts_and_primary_button_are_readable(page_factory, site_url, theme):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}/components.html")
    for kind in ["success", "warning", "danger", "info"]:
        ratio = contrast(page, f".f-alert--{kind} .f-alert__title", f".f-alert--{kind}")
        assert ratio >= 4.5, (kind, ratio)
    assert contrast_on(page, ".f-btn--primary") >= 4.5


def test_matrix_covers_the_layouts():
    layouts = {p for p in PAGES if p.startswith("layouts/")}
    assert layouts == {
        f"layouts/{n}.html"
        for n in [
            "index",
            "reading",
            "docs",
            "margin",
            "split",
            "grid",
            "list",
            "resume",
            "empty",
            "cover",
            "story",
            "panels",
            "deck",
            "app",
            "focus",
            "landing",
        ]
    }


def test_fonts_load(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/index.html")
    page.evaluate("document.fonts.ready")
    loaded = page.evaluate(
        "Promise.all(['16px Geist','16px \"Geist Mono\"','600 16px \"Source Serif 4\"',"
        "'600 16px \"Noto Serif SC\"']"
        ".map(f => document.fonts.load(f, f.includes('Noto') ? '字' : 'a')))"
        ".then(rs => rs.map(r => r.length))"
    )
    assert all(n > 0 for n in loaded), loaded


THEMES = ["dark", "light"]


@pytest.mark.parametrize("theme", THEMES)
def test_text_and_accent_contrast(page_factory, site_url, theme):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}/index.html")
    assert contrast(page, "main p:not(.f-kicker)") >= 4.5
    assert contrast(page, "main a") >= 4.5
    assert contrast(page, ".f-meta") >= 4.5


def test_consumer_css_wins(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/tests/override.html")
    color = page.evaluate("getComputedStyle(document.querySelector('a')).color")
    assert color == "rgb(255, 0, 0)"


def test_contrast_helper_composites_translucent_color(page_factory):
    page = page_factory()
    page.set_content(
        "<body style='background:#fff;margin:0'><p style='color:rgb(0 0 0 / 0.5)'>x</p></body>"
    )
    assert abs(contrast(page, "p") - 3.95) < 0.1


def test_inline_chinese_block_in_english_prose(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/index.html")
    html = (
        '<h2 id="zh-h" lang="zh-Hans">标题</h2>'
        '<p id="zh-p" lang="zh-Hans">正文</p>'
        '<p id="zh-k" class="f-kicker" lang="zh-Hans">标签</p>'
    )
    page.evaluate("(h) => document.querySelector('main').insertAdjacentHTML('beforeend', h)", html)
    lh = (
        "(id) => { const s = getComputedStyle(document.getElementById(id));"
        " return [s.lineHeight, s.fontSize]; }"
    )
    line, size = page.evaluate(lh, "zh-p")
    assert float(line[:-2]) == pytest.approx(float(size[:-2]) * 1.8)
    line, size = page.evaluate(lh, "zh-k")
    assert float(line[:-2]) == pytest.approx(float(size[:-2]))
    h = page.evaluate("getComputedStyle(document.getElementById('zh-h')).letterSpacing")
    assert h in ("normal", "0px")


def test_cast_page(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/cast.html")
    page.wait_for_timeout(300)
    assert page.locator("main .cat").count() == 3
    assert page.locator(".f-footer .cat").count() == 3


def test_site_css_can_resize_footer_cats(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/tests/cat-override.html")
    page.wait_for_timeout(200)
    assert page.evaluate("getComputedStyle(document.querySelector('.cat')).width") == "90px"


@pytest.mark.parametrize("accent", [None, "rose"])
def test_theme_switch_picks_one_value_per_mode(browser, site_url, accent):
    # Every mode resolves to exactly the dark or the light values: auto follows the system and
    # print is always light.
    def colors(theme, scheme="dark", media="screen"):
        ctx = browser.new_context(color_scheme=scheme)
        try:
            page = ctx.new_page()
            page.emulate_media(media=media)
            query = f"theme={theme}" + (f"&accent={accent}" if accent else "")
            page.goto(f"{site_url}/components.html?{query}")
            return page.evaluate(
                "[document.body, document.querySelector('.f-btn--primary')]"
                ".map(e => [getComputedStyle(e).backgroundColor, getComputedStyle(e).color])"
            )
        finally:
            ctx.close()

    dark, light = colors("dark"), colors("light")
    assert dark != light
    assert colors("auto", "dark") == dark
    assert colors("auto", "light") == light
    assert colors("dark", media="print") == light
    assert colors("auto", "dark", media="print") == light


def _leading(page, sel):
    line, size = page.evaluate(
        f"(() => {{ const s = getComputedStyle(document.querySelector({sel!r}));"
        " return [s.lineHeight, s.fontSize].map(parseFloat); })()"
    )
    return line / size


@pytest.mark.parametrize("where", ["html", "subtree"])
def test_chinese_text_outside_prose_gets_the_taller_leading(page_factory, site_url, where):
    page = page_factory(lang="zh" if where == "html" else "en")
    page.goto(f"{site_url}/components.html")
    if where == "subtree":
        page.evaluate("document.querySelector('main').lang = 'zh-Hans'")
    for sel in [".f-card__body p", ".f-alert p", ".f-alert"]:
        assert _leading(page, sel) == pytest.approx(1.8), sel


def test_english_text_keeps_its_leading(page_factory, site_url):
    page = page_factory(lang="en")
    page.goto(f"{site_url}/components.html")
    for sel in [".f-card__body p", ".f-alert p"]:
        assert _leading(page, sel) == pytest.approx(1.6), sel
    # An English block inside a Chinese page.
    page = page_factory(lang="zh")
    page.goto(f"{site_url}/components.html")
    page.evaluate("document.querySelector('.f-alert').lang = 'en'")
    assert _leading(page, ".f-alert p") == pytest.approx(1.6)


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_a_lang_tagged_span_keeps_its_parents_leading(page_factory, site_url, lang):
    page = page_factory(lang=lang)
    page.goto(f"{site_url}/components.html")
    other = "fr" if lang == "en" else "en"
    heights = page.evaluate(f"""() => {{
      const btn = document.querySelector('.f-btn');
      const before = btn.getBoundingClientRect().height;
      btn.insertAdjacentHTML('beforeend', ' <span lang="{other}">x</span>');
      const zh = document.createElement('span');
      zh.lang = 'zh-Hans'; zh.textContent = '猫';
      const h = document.querySelector('h1, h2');
      const hb = h.getBoundingClientRect().height;
      h.append(zh);
      return [before, btn.getBoundingClientRect().height, hb, h.getBoundingClientRect().height];
    }}""")
    assert heights[1] == pytest.approx(heights[0], abs=0.5)
    assert heights[3] == pytest.approx(heights[2], abs=0.5)


MARKUP_PAGES = ["components.html"] + [
    p for p in PAGES if p.startswith("layouts/") and p != "layouts/index.html"
]


def test_every_component_and_layout_shows_its_markup(page_factory, site_url):
    page = page_factory()
    for path in MARKUP_PAGES:
        page.goto(f"{site_url}/{path}")
        blocks = page.evaluate("""[...document.querySelectorAll('details.site-markup')].map(d => ({
            summary: d.querySelector('summary').textContent.trim(),
            escaped: d.querySelector('pre.f-code').children.length === 0,
            text: d.querySelector('pre.f-code').textContent,
            section: d.closest('main.demo > section')?.querySelector('h2')?.textContent ?? null,
          }))""")
        if path == "components.html":
            sections = page.evaluate("document.querySelectorAll('main.demo > section').length")
            assert len(blocks) == sections
            assert len({b["section"] for b in blocks}) == sections
        else:
            assert len(blocks) == 1, path
        for b in blocks:
            assert b["summary"] == "Markup", path
            assert b["escaped"], (path, b["section"])
            assert b["text"].lstrip().startswith("<"), (path, b["section"])


def test_chinese_lines_fill_the_measure(page_factory, site_url):
    # Chinese has no spaces, so it must break between any two characters, not only at punctuation:
    # every line but the last runs (nearly) to the edge.
    page = page_factory(width=390, lang="zh")
    page.goto(f"{site_url}/components.html")
    fills = page.evaluate("""() => {
      const p = document.createElement('p');
      p.lang = 'zh-Hans';
      p.style.cssText = 'width: 300px; margin: 0; padding: 0';
      p.textContent = '红点在墙上，嘟娜在窗台，嘟嘟在沙发下，囔囔在门口，大家都在等，'
        + '等红点再动一下，然后一起扑过去，扑了个空也不要紧。';
      document.querySelector('main').append(p);
      const left = p.getBoundingClientRect().left, text = p.firstChild, ends = new Map();
      for (let i = 0; i < text.length; i++) {
        const r = document.createRange();
        r.setStart(text, i);
        r.setEnd(text, i + 1);
        const box = r.getBoundingClientRect();
        const top = Math.round(box.top);
        ends.set(top, Math.max(ends.get(top) || 0, box.right - left));
      }
      return [...ends.values()].slice(0, -1);
    }""")
    assert len(fills) >= 3
    assert all(f >= 0.9 * 300 for f in fills), fills


@pytest.mark.parametrize(
    "theme, expected",
    [
        ("dark", ["oklch(0.2 0.012 260)", "oklch(0.23 0.012 260)", "oklch(0.26 0.012 260)"]),
        ("light", ["oklch(0.975 0.004 260)", "oklch(0.955 0.006 260)", "oklch(0.995 0.002 260)"]),
    ],
)
def test_neutral_surfaces(page_factory, site_url, theme, expected):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}/components.html")
    got = page.evaluate(
        """['--f-bg', '--f-bg-2', '--f-surface'].map(v => {
          const p = document.createElement('i');
          p.style.background = `var(${v})`;
          document.body.append(p);
          return getComputedStyle(p).backgroundColor;
        })"""
    )
    assert got == expected


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_secondary_text_tokens_are_readable_on_every_neutral(page_factory, site_url, theme):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}/components.html")
    rgb = page.evaluate(
        f"""(() => {{
          const f = ({TO_RGB});
          const resolve = (v, prop) => {{
            const p = document.createElement('i');
            p.style[prop] = `var(${{v}})`;
            document.body.append(p);
            const c = getComputedStyle(p)[prop];
            p.remove();
            return c;
          }};
          const out = {{}};
          for (const bg of ['--f-bg', '--f-bg-2', '--f-surface']) {{
            const back = f(resolve(bg, 'backgroundColor'));
            const over = `rgb(${{back.join(' ')}})`;
            for (const fg of ['--f-fg-2', '--f-fg-3'])
              out[`${{fg}} on ${{bg}}`] = [f(resolve(fg, 'color'), over), back];
          }}
          return out;
        }})()"""
    )
    for pair, (fg, bg) in rgb.items():
        a, b = sorted([_lum(fg), _lum(bg)], reverse=True)
        assert (a + 0.05) / (b + 0.05) >= 4.5, (pair, round((a + 0.05) / (b + 0.05), 2))


@pytest.mark.parametrize(
    "scheme, first", [("light", "oklch(0.99 0.012 260)"), ("dark", "oklch(0.2 0.012 260)")]
)
def test_token_ramp_follows_the_theme_in_effect(browser, site_url, scheme, first):
    # Under auto, the system's scheme decides which ramp is drawn.
    ctx = browser.new_context(color_scheme=scheme)
    try:
        page = ctx.new_page()
        page.goto(f"{site_url}/tokens.html?theme=auto")
        got = page.evaluate(
            "getComputedStyle(document.querySelector('#ramp span')).backgroundColor"
        )
        assert got == first
    finally:
        ctx.close()


def test_chinese_text_shows_the_html_element_name(page_factory, site_url):
    page = page_factory(lang="zh")
    page.goto(f"{site_url}/index.html")
    texts = page.evaluate(
        "[...document.querySelectorAll('main [data-zh]')].map(e => e.textContent)"
    )
    assert any("两者都只在 <html> 上生效" in t for t in texts)


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_code_in_a_table_cell_never_breaks_mid_word(page_factory, site_url, lang):
    page = page_factory(width=390, lang=lang)
    page.goto(f"{site_url}/index.html")
    # Each code fragment in the Behavior table: the pieces it wraps into must be whole words
    # split only after a hyphen (no line starting or ending inside a word).
    lines = page.evaluate("""() => [...document.querySelectorAll('#behavior td code')]
    .flatMap(c => {
      const r = document.createRange(), t = c.firstChild, tops = [];
      if (!t) return [];
      let line = '', top = null;
      for (let i = 0; i < t.length; i++) {
        r.setStart(t, i); r.setEnd(t, i + 1);
        const y = Math.round(r.getBoundingClientRect().top);
        if (top !== null && y !== top) { tops.push(line); line = ''; }
        top = y; line += t.data[i];
      }
      tops.push(line);
      return tops.length > 1 ? [tops] : [];
    })""")
    for pieces in lines:
        for piece in pieces[:-1]:
            assert piece.endswith(("-", " ", "/", ".")), pieces


@pytest.mark.parametrize("width", [390, 1280])
def test_a_wide_table_grows_past_the_text_column(page_factory, site_url, width):
    page = page_factory(width=width)
    page.goto(f"{site_url}/index.html")
    table, text = page.evaluate(
        "['#behavior table.f-wide', '#behavior > p'].map(s =>"
        " document.querySelector(s).getBoundingClientRect().toJSON())"
    )
    if width == 1280:
        assert table["width"] > text["width"] + 100
        assert abs((table["left"] + table["right"]) / 2 - (text["left"] + text["right"]) / 2) < 2
    else:
        assert table["left"] >= 0 and table["right"] <= width


# Each demo code block on the components page, measured: what it copies, its numbers, its bar.
CODE_BLOCKS = """() => {
  const hit = (a, b) =>
    a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  return [...document.querySelectorAll('#code-options pre:has(> code)')].map(pre => {
    const code = pre.querySelector(':scope > code'), lines = [...code.children];
    const sel = getSelection();
    sel.selectAllChildren(pre);
    const copied = sel.toString();
    sel.removeAllRanges();
    const btn = pre.querySelector(':scope > .f-code-copy')?.getBoundingClientRect();
    const walk = document.createTreeWalker(code, NodeFilter.SHOW_TEXT), texts = [];
    while (walk.nextNode()) {
      const r = document.createRange();
      r.selectNodeContents(walk.currentNode);
      texts.push(...[...r.getClientRects()].filter(t => t.width > 0));
    }
    const bar = getComputedStyle(pre, '::before'), box = pre.getBoundingClientRect();
    return {
      code: code.textContent,
      copied,
      title: pre.dataset.fCodeTitle ?? null,
      numbers: lines.map(l => getComputedStyle(l, '::before').content),
      tops: lines.map(l => l.getBoundingClientRect().top),
      overflow: Math.max(code.scrollWidth - code.clientWidth, pre.scrollWidth - pre.clientWidth),
      wraps: getComputedStyle(code).whiteSpace === 'pre-wrap',
      dots: (bar.backgroundImage.match(/radial-gradient/g) || []).length,
      barHeight: parseFloat(bar.height) || 0,
      titleRight: box.right - 1 - parseFloat(bar.paddingRight),
      btn: btn ? { left: btn.left, bottom: btn.bottom } : null,
      btnHitsCode: !!btn && texts.some(t => hit(t, btn)),
      codeTop: Math.min(...texts.map(t => t.top)),
    };
  });
}"""


@pytest.mark.parametrize(("width", "lang"), [(390, "zh"), (1280, "en")])
def test_code_block_options(page_factory, site_url, width, lang):
    page = page_factory(width=width, lang=lang)
    page.goto(f"{site_url}/components.html")
    settle(page)
    numbered, wrapped, opted_out, titled, titled_zh, framed = page.evaluate(CODE_BLOCKS)

    # Numbers come from a counter, so copying the block copies only the code, title included.
    for b in (numbered, wrapped):
        assert b["numbers"] == ["counter(f-code-ln)"] * len(b["numbers"])
    for b in (numbered, wrapped, opted_out, titled, titled_zh, framed):
        assert b["code"] in b["copied"]
        assert not any(c.isdigit() for c in b["copied"].replace(b["code"], ""))
        if b["title"]:
            assert b["title"] not in b["copied"]
    # The page default numbers the article's code; a block's data-f-code-ln="false" opts out.
    assert set(opted_out["numbers"]) <= {"none", "normal"}

    # Wrapped: no sideways scroll, and the empty line keeps its own row and its newline.
    for b in (wrapped, framed):
        assert b["wraps"] and b["overflow"] <= 0
        assert "\n\n" in b["copied"]
        assert b["tops"][1] < b["tops"][2] < b["tops"][3]
    assert numbered["overflow"] > 0 and not numbered["wraps"]

    # A title or frame draws a bar; the frame adds three dots. The Copy button sits in the bar,
    # clear of the title and the code; unframed, it stays clear of the wrapped first line.
    assert framed["dots"] == 3 and titled["dots"] == 0 and wrapped["barHeight"] == 0
    for b in (titled, titled_zh, framed):
        assert b["barHeight"] > 0 and b["codeTop"] >= b["barHeight"]
    for b in (wrapped, titled, framed):
        assert not b["btnHitsCode"]
    for b in (titled, framed):
        assert b["btn"]["bottom"] <= b["codeTop"] and b["titleRight"] <= b["btn"]["left"]

    # The block wins over its container either way, and highlighter numbers are not doubled.
    page.evaluate("""() => document.querySelector('#code-options article').insertAdjacentHTML(
      'beforeend', '<div data-f-code-ln="false"><pre id="t-on"><code data-f-code-ln="true">'
        + '<span class="line">a</span></code></pre></div><pre id="t-native"><code>'
        + '<span class="giallo-l"><span class="giallo-ln">1</span>b</span></code></pre>')""")
    on, native = page.evaluate(
        "['#t-on .line', '#t-native .giallo-l'].map(s =>"
        " getComputedStyle(document.querySelector(s), '::before').content)"
    )
    assert on == "counter(f-code-ln)" and native in ("none", "normal")

    # A long title ends in an ellipsis without widening anything.
    page.evaluate(
        "document.querySelector('#code-options [data-f-code-title]').dataset.fCodeTitle ="
        " 'src/' + 'very-long-directory-name/'.repeat(12) + 'main.rs'"
    )
    no_hscroll(page)
    assert (
        page.evaluate(
            "getComputedStyle(document.querySelector('#code-options [data-f-code-title]'),"
            " '::before').textOverflow"
        )
        == "ellipsis"
    )
