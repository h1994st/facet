"""The Focus layout: a centered page about one thing (here, Duna's contact page)."""

import pytest
from checks import contrast, no_hscroll

PAGE = "layouts/focus.html"


@pytest.mark.parametrize("width", [390, 1280])
def test_centered_in_the_window(page_factory, site_url, width):
    page = page_factory(width=width)
    page.goto(f"{site_url}/{PAGE}")
    title, link, win = page.evaluate(
        "[...['.f-focus__title', '.f-focus__link'].map(s =>"
        " document.querySelector(s).getBoundingClientRect().toJSON()), innerWidth]"
    )
    for box in (title, link):
        assert abs((box["left"] + box["right"]) / 2 - win / 2) < 2


def test_the_link_mails_the_real_address_and_hides_the_typing(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/{PAGE}")
    link = page.locator(".f-focus__link")
    assert link.get_attribute("href") == "mailto:meow@example.com"
    assert link.locator(".f-visually-hidden").inner_text() == "meow@example.com"
    typed = page.locator(".f-focus__typed")
    assert typed.get_attribute("data-f-type")
    assert page.evaluate(
        "document.querySelector('.f-focus__typed').closest('[aria-hidden=\"true\"]') !== null"
    )


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_typed_part_wears_the_accent_and_the_hint_is_readable(page_factory, site_url, theme):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}/{PAGE}")
    accent = page.evaluate(
        "(() => { const p = document.createElement('i'); p.style.color = 'var(--f-accent)';"
        " document.body.append(p); return getComputedStyle(p).color; })()"
    )
    assert (
        page.evaluate("getComputedStyle(document.querySelector('.f-focus__typed')).color") == accent
    )
    assert contrast(page, ".f-focus__hint") >= 4.5
    assert contrast(page, ".f-focus__link") >= 4.5


def test_long_phrase_never_scrolls_sideways(page_factory, site_url):
    page = page_factory(width=390)
    page.goto(f"{site_url}/{PAGE}")
    page.evaluate(
        "document.querySelector('.f-focus__typed').textContent ="
        " 'you-can-write-to-any-name-here-and-it-still-reaches-a-cat-who-is-asleep'"
    )
    no_hscroll(page)


def test_credits_its_inspiration(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/{PAGE}")
    assert page.locator('.site-credit a[href^="https://mldangelo.com/"]').count() == 1


def test_listed_on_the_layouts_page(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/layouts/index.html")
    assert page.locator('a.lx-item[href="focus.html"]').count() == 1
