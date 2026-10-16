"""The JS modules' contract: idempotent init, cleanup, isolation, and per-module fixes."""

import pytest
from playwright.sync_api import expect

FACET = "import('/dist/js/facet.js')"


def theme(page):
    return page.evaluate("document.documentElement.dataset.theme")


def test_init_twice_still_advances_the_toggle_one_step(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/components.html")
    page.evaluate(f"{FACET}.then((m) => {{ m.init(); m.init(); }})")
    assert theme(page) == "dark"
    page.click("[data-f-theme-toggle]")
    assert theme(page) == "light"


def test_init_twice_keeps_one_set_of_panel_dots(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/layouts/panels.html")
    dots = "document.querySelectorAll('nav.f-dots button').length"
    assert page.evaluate(dots) == 5
    page.evaluate(f"{FACET}.then((m) => {{ m.init(); m.init(); }})")
    assert page.evaluate(dots) == 5


def test_cleanup_removes_listeners_and_generated_markup(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/layouts/panels.html")
    page.evaluate(f"{FACET}.then((m) => m.cleanup())")
    assert page.evaluate("document.querySelectorAll('nav.f-dots button').length") == 0
    assert "is-ready" not in page.locator("[data-f-panels]").get_attribute("class")

    page.goto(f"{site_url}/components.html")
    card = page.locator("#demo-card")
    card.hover()
    page.evaluate(f"{FACET}.then((m) => m.cleanup())")
    assert "is-hot" not in card.get_attribute("class")
    page.click("[data-f-theme-toggle]")
    assert theme(page) == "dark"
    page.mouse.move(0, 0)
    card.hover()
    assert "is-hot" not in card.get_attribute("class")


def test_a_failing_module_does_not_stop_the_others(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/layouts/panels.html")
    page.evaluate(
        f"""{FACET}.then((m) => {{
          m.cleanup();
          m.init({{ querySelectorAll(sel) {{
            if (sel.includes('data-f-liquid')) throw new Error('liquid boom');
            return document.querySelectorAll(sel);
          }} }});
        }})"""
    )
    assert any("liquid boom" in e for e in page.errors), page.errors
    page.errors.clear()
    # panels runs after liquid.
    assert page.evaluate("document.querySelectorAll('nav.f-dots button').length") == 5


def test_only_the_current_deck_caption_is_reachable(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/layouts/deck.html")
    caps = "[...document.querySelectorAll('.f-deck__cap')].map((c) => c.inert)"
    states = page.evaluate(caps)
    assert len(states) > 2
    assert states == [False] + [True] * (len(states) - 1)
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(900)
    assert page.evaluate(caps) == [True, False] + [True] * (len(states) - 2)


def test_theme_snippet_presets_and_toggle_is_labeled(page_factory, site_url):
    page = page_factory()
    page.add_init_script("localStorage.setItem('facet-theme', 'light')")
    page.add_init_script(
        "new MutationObserver((_, obs) => { if (document.body) {"
        " window.__atBody = document.documentElement.dataset.theme; obs.disconnect() } })"
        ".observe(document, { childList: true, subtree: true })"
    )
    page.goto(f"{site_url}/tests/theme-snippet.html")
    page.wait_for_function("document.querySelector('[data-f-theme-toggle]').ariaLabel")
    assert page.evaluate("window.__atBody") == "light"
    btn = page.locator("[data-f-theme-toggle]")
    assert btn.get_attribute("aria-label") == "Theme: Light"
    assert btn.inner_text() == "Light"


@pytest.mark.parametrize("stored", ["nope", "", "Light"])
def test_bogus_stored_theme_is_ignored(page_factory, site_url, stored):
    page = page_factory()
    page.add_init_script(f"localStorage.setItem('facet-theme', {stored!r})")
    page.goto(f"{site_url}/tests/theme-snippet.html")
    page.wait_for_function("document.querySelector('[data-f-theme-toggle]').ariaLabel")
    assert theme(page) == "dark"
    assert page.get_attribute("[data-f-theme-toggle]", "aria-label") == "Theme: Dark"


def test_scrollspy_matches_chinese_ids(page_factory, site_url):
    page = page_factory(width=1280)
    page.goto(f"{site_url}/tests/scrollspy-zh.html")
    page.evaluate("document.getElementById('安装').scrollIntoView()")
    page.wait_for_timeout(200)
    current = page.evaluate(
        "document.querySelector('[data-f-scrollspy] [aria-current]').textContent.trim()"
    )
    assert current == "安装"


def test_panel_video_has_a_pause_control(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/layouts/panels.html")
    btn = page.locator("[data-f-panel-toggle]")
    paused = "document.querySelector('.f-panel video').paused"
    page.wait_for_function(f"!{paused}")
    assert btn.is_visible()
    expect(btn).to_have_text("Pause")
    btn.click()
    assert page.evaluate(paused) is True
    expect(btn).to_have_text("Play")
    btn.click()
    page.wait_for_function(f"!{paused}")
    expect(btn).to_have_text("Pause")


def test_panel_video_stays_paused_under_reduced_motion(page_factory, site_url):
    page = page_factory(reduced_motion=True)
    page.goto(f"{site_url}/layouts/panels.html")
    page.wait_for_timeout(300)
    assert page.evaluate("document.querySelector('.f-panel video').paused")
    assert not page.locator("[data-f-panel-toggle]").is_visible()
