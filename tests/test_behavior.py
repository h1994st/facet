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


def test_sheet_is_centered_in_viewport(page_factory, site_url):
    page = page_factory(width=1280)
    page.goto(f"{site_url}/components.html")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.click("#demo-open-sheet")
    top = page.evaluate("document.querySelector('.f-sheet').getBoundingClientRect().top")
    assert 0 <= top < 900
