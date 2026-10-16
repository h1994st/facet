import pytest
from checks import no_hscroll


@pytest.mark.parametrize("width", [390, 860, 1280])
def test_index_loads(page_factory, site_url, width):
    page = page_factory(width=width)
    page.goto(f"{site_url}/index.html")
    no_hscroll(page)
    assert page.errors == []


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


from checks import contrast  # noqa: E402

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
    page.evaluate(
        "document.querySelector('main').insertAdjacentHTML("
        "'beforeend', '<h2 lang=\"zh-Hans\">标题</h2><p lang=\"zh-Hans\">正文</p>')"
    )
    p = page.evaluate(
        "(() => { const s = getComputedStyle(document.querySelector('p[lang]'));"
        " return [s.lineHeight, s.fontSize]; })()"
    )
    assert float(p[0][:-2]) == pytest.approx(float(p[1][:-2]) * 1.8)
    h = page.evaluate("getComputedStyle(document.querySelector('h2[lang]')).letterSpacing")
    assert h in ("normal", "0px")
