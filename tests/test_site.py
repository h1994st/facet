from pathlib import Path

import pytest
from checks import cat_text_overlaps, contrast, contrast_on, no_hscroll

SITE = Path(__file__).resolve().parents[1] / "site"
# Every reference-site page except the test fixtures; the symlinked dist/ and assets/ are skipped.
PAGES = sorted(
    p.relative_to(SITE).as_posix()
    for p in SITE.rglob("*.html")
    if p.relative_to(SITE).parts[0] not in ("tests", "dist", "assets")
)


@pytest.mark.parametrize("lang", ["en", "zh"])
@pytest.mark.parametrize("theme", ["dark", "light"])
@pytest.mark.parametrize("width", [390, 860, 1280])
@pytest.mark.parametrize("path", PAGES)
def test_page_matrix(page_factory, site_url, path, width, theme, lang):
    page = page_factory(width=width, theme=theme, lang=lang)
    page.goto(f"{site_url}/{path}")
    page.wait_for_timeout(100)
    no_hscroll(page)
    assert page.errors == []


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
@pytest.mark.parametrize("accent", ACCENTS)
def test_every_accent_is_readable(page_factory, site_url, accent, theme):
    page = page_factory(theme=theme, accent=accent)
    page.goto(f"{site_url}/color.html")
    assert page.evaluate("document.documentElement.dataset.accent") == accent
    assert contrast_on(page, ".f-btn--primary") >= 4.5
    assert contrast(page, "main a") >= 4.5


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_meta_text_is_readable(page_factory, site_url, theme):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}/index.html")
    assert contrast(page, ".f-meta") >= 4.5


@pytest.mark.parametrize("path", PAGES)
def test_every_page_has_toolbar(page_factory, site_url, path):
    page = page_factory()
    page.goto(f"{site_url}/{path}")
    assert page.locator("header.site-bar").count() == 1
    assert page.locator(".site-bar .site-dot").count() == len(ACCENTS)


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


def test_toolbar_marks_one_current_page(page_factory, site_url):
    linked = {
        "index.html",
        "tokens.html",
        "color.html",
        "type.html",
        "components.html",
        "cast.html",
        "seo.html",
    }
    for path in PAGES:
        page = page_factory()
        page.goto(f"{site_url}/{path}")
        count = page.locator('.site-bar a[aria-current="page"]').count()
        expected = 1 if path in linked or path.startswith("layouts/") else 0
        assert count == expected, (path, count)
        if path == "layouts/index.html":
            label = page.locator('.site-bar a[aria-current="page"]').inner_text()
            assert label == "Layouts"


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
        "dark",
        "en",
        None,
    ]


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


@pytest.mark.parametrize("lang", ["en", "zh"])
@pytest.mark.parametrize("theme", THEMES)
def test_primary_button_contrast(page_factory, site_url, theme, lang):
    page = page_factory(theme=theme, lang=lang)
    page.goto(f"{site_url}/components.html")
    assert contrast_on(page, ".f-btn--primary") >= 4.5


@pytest.mark.parametrize("width", [390, 1280])
def test_cats_never_cover_text(page_factory, site_url, width):
    from checks import cat_text_overlaps

    for path in PAGES:
        page = page_factory(width=width)
        page.goto(f"{site_url}/{path}")
        page.wait_for_timeout(300)
        assert cat_text_overlaps(page) == 0, path


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


@pytest.mark.parametrize("width", [390, 1280])
@pytest.mark.parametrize("path", MARKUP_PAGES)
def test_open_markup_never_scrolls_the_page_sideways(page_factory, site_url, path, width):
    page = page_factory(width=width)
    page.goto(f"{site_url}/{path}")
    page.evaluate("document.querySelectorAll('details.site-markup').forEach(d => d.open = true)")
    no_hscroll(page)
    page.wait_for_timeout(300)
    assert cat_text_overlaps(page) == 0
    # Nor widen a container that clips (a full-screen panel or deck stage hides the overflow).
    for sel in ["details.site-markup", "main h2"]:
        right = page.evaluate(
            f"Math.max(0, ...[...document.querySelectorAll({sel!r})]"
            ".filter(e => e.checkVisibility()).map(e => e.getBoundingClientRect().right))"
        )
        assert right <= width, sel
    # Long lines scroll inside the code block.
    for overflow in page.evaluate(
        "[...document.querySelectorAll('details.site-markup pre')]"
        ".map(p => getComputedStyle(p).overflowX)"
    ):
        assert overflow == "auto"
