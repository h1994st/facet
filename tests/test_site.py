from pathlib import Path

import pytest
from checks import no_hscroll

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


from checks import contrast, contrast_on  # noqa: E402

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
