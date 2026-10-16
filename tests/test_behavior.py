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
