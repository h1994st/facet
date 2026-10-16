"""The hero card (a deep shade of the accent) and the Landing layout built around it."""

import re

import pytest
from checks import TO_RGB, _lum, contrast, contrast_on, no_hscroll

PAGE = "layouts/landing.html"
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
def test_card_text_is_readable_for_every_accent(page_factory, site_url, accent, theme):
    page = page_factory(theme=theme, accent=accent)
    page.goto(f"{site_url}/{PAGE}")
    for sel in (".f-hero__title", ".f-hero__lead", ".f-hero__body", ".f-hero__kicker"):
        assert contrast(page, sel, ".f-hero") >= 4.5, sel
    assert contrast_on(page, ".f-hero .f-btn--primary") >= 4.5


def test_card_is_deep_on_both_themes(page_factory, site_url):
    fills = []
    for theme in ("dark", "light"):
        page = page_factory(theme=theme, accent="moss")
        page.goto(f"{site_url}/{PAGE}")
        fills.append(
            page.evaluate("getComputedStyle(document.querySelector('.f-hero')).backgroundColor")
        )
    assert fills[0] == fills[1]
    lightness, chroma, hue = map(
        float, re.match(r"oklch\(([\d.]+) ([\d.]+) ([\d.]+)", fills[0]).groups()
    )
    assert lightness == pytest.approx(0.42)
    assert chroma == pytest.approx(0.06)
    assert hue == pytest.approx(130)


def oklch(color):
    return tuple(map(float, re.match(r"oklch\(([\d.]+) ([\d.]+) ([\d.]+)", color).groups()))


def test_card_falls_back_to_slate_without_relative_colors(page_factory, site_url):
    # A browser without relative colors cannot parse oklch(from ...): renaming the function
    # makes Chromium behave the same, in @supports and in every declaration.
    page = page_factory(accent="moss")

    def no_relative_colors(route):
        css = route.fetch().text().replace("oklch(from", "nope(from")
        route.fulfill(body=css, content_type="text/css")

    page.route("**/dist/facet.css", no_relative_colors)
    page.goto(f"{site_url}/{PAGE}")
    fill = page.evaluate("getComputedStyle(document.querySelector('.f-hero')).backgroundColor")
    assert fill == "oklch(0.42 0.06 255)"
    for sel in (".f-hero__title", ".f-hero__lead", ".f-hero__body", ".f-hero__kicker"):
        assert contrast(page, sel, ".f-hero") >= 4.5, sel
    assert contrast_on(page, ".f-hero .f-btn--primary") >= 4.5


def test_card_follows_a_subtree_accent(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/{PAGE}")
    page.evaluate(
        "document.querySelector('.f-hero').parentElement.style"
        ".setProperty('--f-accent', 'oklch(0.76 0.06 15)')"
    )
    fill, ink = page.evaluate(
        "(() => { const s = getComputedStyle(document.querySelector('.f-hero'));"
        " return [s.backgroundColor, s.color]; })()"
    )
    assert oklch(fill) == pytest.approx((0.42, 0.06, 15))
    assert oklch(ink)[2] == pytest.approx(15)


def test_card_prints_with_its_fill(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/{PAGE}")
    page.emulate_media(media="print")
    assert (
        page.evaluate("getComputedStyle(document.querySelector('.f-hero')).printColorAdjust")
        == "exact"
    )


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_plain_button_hover_shows_on_the_card(page_factory, site_url, theme):
    page = page_factory(theme=theme, reduced_motion=True)
    page.goto(f"{site_url}/{PAGE}")
    page.evaluate(
        "document.querySelector('.f-hero__actions').insertAdjacentHTML('beforeend',"
        ' \'<a class="f-btn" id="plain" href="#">Plain</a>\')'
    )
    page.hover("#plain")
    fill, hover = page.evaluate(
        f"""(() => {{
          const f = ({TO_RGB});
          const card = f(getComputedStyle(document.querySelector('.f-hero')).backgroundColor);
          const own = getComputedStyle(document.querySelector('#plain')).backgroundColor;
          return [card, f(own, `rgb(${{card.join(' ')}})`)];
        }})()"""
    )
    a, b = sorted([_lum(fill), _lum(hover)], reverse=True)
    assert (a + 0.05) / (b + 0.05) >= 1.2


@pytest.mark.parametrize("accent", ["stone", "graphite"])
def test_near_neutral_accents_stay_near_neutral(page_factory, site_url, accent):
    page = page_factory(accent=accent)
    page.goto(f"{site_url}/{PAGE}")
    fill = page.evaluate("getComputedStyle(document.querySelector('.f-hero')).backgroundColor")
    chroma = float(re.match(r"oklch\([\d.]+ ([\d.]+)", fill).group(1))
    assert chroma <= 0.03, fill


def test_card_stacks_on_a_phone(page_factory, site_url):
    page = page_factory(width=390)
    page.goto(f"{site_url}/{PAGE}")
    no_hscroll(page)
    text, media = page.evaluate(
        "['.f-hero__title', '.f-hero__media']"
        ".map(s => document.querySelector(s).getBoundingClientRect().toJSON())"
    )
    assert media["top"] >= text["bottom"]


@pytest.mark.parametrize("width, side_by_side", [(1280, True), (390, False)])
def test_recent_list_sits_beside_its_heading_on_wide_screens(
    page_factory, site_url, width, side_by_side
):
    page = page_factory(width=width)
    page.goto(f"{site_url}/{PAGE}")
    head, items = page.evaluate(
        "['.f-landing__head', '.f-landing__list']"
        ".map(s => document.querySelector(s).getBoundingClientRect().toJSON())"
    )
    assert (items["left"] > head["right"]) is side_by_side


def test_landing_credits_its_inspiration_and_is_listed(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/{PAGE}")
    assert page.locator('.site-credit a[href="https://mldangelo.com/"]').count() == 1
    page.goto(f"{site_url}/layouts/index.html")
    assert page.locator('a.lx-item[href="landing.html"]').count() == 1
