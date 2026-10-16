from checks import focus_ring


def test_theme_toggle_cycles(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/components.html")
    btn = page.locator("[data-f-theme-toggle]").first
    seen = []
    for _ in range(3):
        btn.click()
        seen.append(page.evaluate("document.documentElement.dataset.theme"))
    assert seen == ["light", "auto", "dark"]
    page.reload()
    assert page.evaluate("document.documentElement.dataset.theme") == "dark"


def test_controls_show_focus_ring(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/components.html")
    for sel in [
        "#demo-btn",
        "#demo-chip",
        "#demo-segmented button",
        "#demo-input",
        "[data-f-theme-toggle]",
    ]:
        page.keyboard.press("Tab")  # ensure keyboard modality
        assert not focus_ring(page, sel).startswith("none"), sel


def test_liquid_hover_sets_state(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/components.html")
    card = page.locator("#demo-card")
    card.hover()
    assert "is-hot" in card.get_attribute("class")
    page.mouse.move(0, 0)
    assert "is-hot" not in card.get_attribute("class")


def _sheet_box(page):
    page.evaluate(
        "Promise.all(document.querySelector('.f-sheet').getAnimations().map((a) => a.finished))"
    )
    return page.evaluate(
        """() => {
            const r = document.querySelector('.f-sheet').getBoundingClientRect();
            return {left: r.left, top: r.top, width: r.width, height: r.height,
                    bottom: r.bottom, vw: innerWidth, vh: innerHeight};
        }"""
    )


def test_sheet_is_centered_in_viewport(page_factory, site_url):
    page = page_factory(width=1280)
    page.goto(f"{site_url}/components.html")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.click("#demo-open-sheet")
    b = _sheet_box(page)
    assert abs(b["left"] - (b["vw"] - b["width"]) / 2) < 2
    assert abs(b["top"] - (b["vh"] - b["height"]) / 2) < 2


def test_sheet_is_a_bottom_sheet_on_phones(page_factory, site_url):
    page = page_factory(width=375)
    page.goto(f"{site_url}/components.html")
    page.click("#demo-open-sheet")
    b = _sheet_box(page)
    assert abs(b["bottom"] - b["vh"]) < 2
    assert abs(b["width"] - b["vw"]) < 2


def test_sheet_locks_page_scroll_while_open(page_factory, site_url):
    page = page_factory(width=1280)
    page.goto(f"{site_url}/components.html")
    overflow = "getComputedStyle(document.documentElement).overflow"
    assert page.evaluate(overflow) != "hidden"
    page.click("#demo-open-sheet")
    assert page.evaluate(overflow) == "hidden"
    page.click("#demo-close-sheet")
    assert page.evaluate(overflow) != "hidden"
