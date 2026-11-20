"""Syntax colors and the diff view on the components page."""

import re
from pathlib import Path

import pytest
from checks import contrast_in_place, focus_ring, no_hscroll

ROOT = Path(__file__).resolve().parents[1]
DIFF = "#demo-diff"
TOKENS = [
    "keyword",
    "string",
    "number",
    "constant",
    "type",
    "function",
    "property",
    "comment",
    "punctuation",
]


def test_syntax_colors_stay_low_in_chroma():
    css = (ROOT / "src/css/10-tokens.css").read_text()
    values = re.findall(r"--f-syn-[\w-]+:([^;]*);", css)
    chromas = [float(c) for v in values for c in re.findall(r"oklch\([\d.]+ ([\d.]+)", v)]
    assert chromas and max(chromas) <= 0.08


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_syntax_colors_are_readable_on_code_and_diff_lines(page_factory, site_url, theme):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}/components.html")
    seen = set()
    for scope in ["#demo-syntax", *(f"{DIFF} .f-diff__line{k}" for k in ["", "--add", "--del"])]:
        for token in TOKENS:
            sel = f"{scope} .f-syn-{token}"
            if page.locator(sel).count():
                seen.add(token)
                assert contrast_in_place(page, sel) >= 4.5, (theme, sel)
    assert seen == set(TOKENS)
    for sel in [f"{DIFF} .f-diff__hunk", f"{DIFF} .f-diff__added", f"{DIFF} .f-diff__removed"]:
        assert contrast_in_place(page, sel) >= 4.5, (theme, sel)


def pseudo(page, sel, which):
    return page.evaluate(f"getComputedStyle(document.querySelector({sel!r}), '::{which}').content")


def test_lines_carry_numbers_and_markers_that_are_not_copied(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/components.html")
    add = f"{DIFF} .f-diff__line--add"
    rem = f"{DIFF} .f-diff__line--del"
    ctx = f"{DIFF} .f-diff__line:not(.f-diff__line--add, .f-diff__line--del)"
    # The marker is text, so meaning never rests on color alone.
    assert pseudo(page, f"{add} > code", "before").startswith('"+"')
    assert pseudo(page, f"{rem} > code", "before").startswith('"−"')
    assert pseudo(page, f"{ctx} > code", "before") in ('""', "none")
    # Numbers come from data-old and data-new (the first context line is 12 in both).
    assert pseudo(page, ctx, "before") == pseudo(page, ctx, "after") == '"12"'
    # Added and removed rows are tinted; context rows are not.
    bg = "(s) => getComputedStyle(document.querySelector(s)).backgroundColor"
    assert page.evaluate(bg, add) != page.evaluate(bg, rem)
    assert page.evaluate(bg, ctx) == "rgba(0, 0, 0, 0)"
    copied = page.evaluate(
        f"""(() => {{ const s = getSelection();
          s.selectAllChildren(document.querySelector('{DIFF} .f-diff__lines'));
          const t = s.toString(); s.removeAllRanges(); return t; }})()"""
    )
    assert "pub fn follow" in copied
    assert not re.search(r"^\s*(\d+|[+−])", copied.split("\n")[1])


def test_long_lines_scroll_inside_on_wide_screens_and_wrap_on_phones(page_factory, site_url):
    wide = page_factory(width=1280)
    wide.goto(f"{site_url}/components.html")
    body = f"document.querySelector('{DIFF} .f-diff__body')"
    assert wide.evaluate(f"{body}.scrollWidth > {body}.clientWidth")
    # Every row spans the scrolled width, so its tint does too.
    widths = wide.evaluate(
        f"new Set([...document.querySelectorAll('{DIFF} .f-diff__line')]"
        ".map(r => Math.round(r.getBoundingClientRect().width))).size"
    )
    assert widths == 1
    no_hscroll(wide)
    for lang in ["en", "zh"]:
        phone = page_factory(width=390, lang=lang)
        phone.goto(f"{site_url}/components.html")
        assert phone.evaluate(f"{body}.scrollWidth <= {body}.clientWidth")
        tallest, lh = phone.evaluate(
            f"[Math.max(...[...document.querySelectorAll('{DIFF} .f-diff__line--add')]"
            ".map(r => r.getBoundingClientRect().height)),"
            f" parseFloat(getComputedStyle(document.querySelector('{DIFF} .f-diff__lines'))"
            ".lineHeight)]"
        )
        assert tallest >= 3 * lh, "the long added line wraps"
        no_hscroll(phone)


def test_wrap_modifier_wraps_at_any_width(page_factory, site_url):
    page = page_factory(width=1280)
    page.goto(f"{site_url}/components.html")
    page.evaluate(f"document.querySelector({DIFF!r}).classList.add('f-diff--wrap')")
    body = f"document.querySelector('{DIFF} .f-diff__body')"
    assert page.evaluate(f"{body}.scrollWidth <= {body}.clientWidth")


def test_files_collapse_from_the_header_without_js(page_factory, site_url):
    page = page_factory(js=False)
    page.goto(f"{site_url}/components.html")
    assert page.is_visible(f"{DIFF} .f-diff__lines")
    page.click(f"{DIFF} > summary")
    assert not page.is_visible(f"{DIFF} .f-diff__lines")
    assert not page.is_visible("#demo-diff-closed .f-diff__lines")
    page.click("#demo-diff-closed > summary")
    assert page.is_visible("#demo-diff-closed .f-diff__lines")
    page.keyboard.press("Tab")
    assert not focus_ring(page, f"{DIFF} > summary").startswith("none")


@pytest.mark.parametrize("reduced", [False, True])
def test_load_more_row_shows_a_busy_state(page_factory, site_url, reduced):
    page = page_factory(reduced_motion=reduced)
    page.goto(f"{site_url}/components.html")
    more = f"{DIFF} .f-diff__more"
    assert page.inner_text(more) == "Show 24 more lines"
    assert not focus_ring(page, f"{more} > button").startswith("none")
    assert pseudo(page, f"{more} > button", "before") in ("none", "normal")
    page.evaluate(f"document.querySelector({more!r}).setAttribute('aria-busy', 'true')")
    assert pseudo(page, f"{more} > button", "before") == '""'
    name = page.evaluate(
        f"getComputedStyle(document.querySelector('{more} > button'), '::before').animationName"
    )
    assert name == ("none" if reduced else "f-diff-spin")
