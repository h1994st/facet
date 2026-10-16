"""Social icon links and the divider."""

import re
from pathlib import Path

import pytest
from checks import contrast, focus_ring

NAMES = sorted(p.stem for p in (Path(__file__).resolve().parents[1] / "src/icons").glob("*.svg"))


def test_icons_css_works_on_its_own(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/tests/icons-only.html")
    box, mask = page.evaluate(
        "(() => { const e = document.getElementById('icon'); const s = getComputedStyle(e);"
        " return [e.getBoundingClientRect().width, s.maskImage || s.webkitMaskImage]; })()"
    )
    assert box == 32
    assert mask.startswith('url("data:image/svg+xml')


def test_every_icon_is_shown_on_the_components_page(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/components.html")
    shown = page.evaluate(
        "[...document.querySelectorAll('#social .f-icon')].map(e => [e.className,"
        " getComputedStyle(e).maskImage || getComputedStyle(e).webkitMaskImage])"
    )
    names = {re.search(r"f-icon--([a-z-]+)", c).group(1) for c, _ in shown}
    assert set(NAMES) <= names
    assert all(m.startswith("url(") for _, m in shown)


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_social_links_are_round_readable_and_light_up(page_factory, site_url, theme):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}/components.html")
    link = "#social .f-social__link"
    w, h, radius = page.evaluate(
        f"(() => {{ const e = document.querySelector({link!r});"
        " const r = e.getBoundingClientRect();"
        " return [r.width, r.height, getComputedStyle(e).borderTopLeftRadius]; })()"
    )
    assert (w, h) == (44, 44) and radius == "50%"
    assert contrast(page, link) >= 3
    page.hover(link)
    page.wait_for_timeout(300)
    probe = page.evaluate(
        "(() => { const p = document.createElement('i');"
        " p.style.cssText = 'color: var(--f-accent); background: var(--f-accent-soft)';"
        " document.body.append(p); const s = getComputedStyle(p);"
        " return [s.color, s.backgroundColor]; })()"
    )
    got = page.evaluate(
        f"(() => {{ const s = getComputedStyle(document.querySelector({link!r}));"
        " return [s.color, s.backgroundColor]; })()"
    )
    assert got == probe
    ring = focus_ring(page, link)
    assert not ring.startswith("none"), ring


def test_social_links_have_names(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/components.html")
    for name in page.locator("#social .f-social__link").all():
        assert name.inner_text().strip(), "each link needs a visually hidden label"
        assert name.locator(".f-icon").get_attribute("aria-hidden") == "true"


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_divider_draws_two_rules_around_its_text(page_factory, site_url, theme):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}/components.html")
    before, after = page.evaluate(
        "['::before', '::after'].map(p => getComputedStyle(document.querySelector("
        "'#divider .f-divider'), p).height)"
    )
    assert before == after == "1px"
    assert contrast(page, "#divider .f-divider") >= 4.5
