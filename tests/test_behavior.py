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


CURRENT_IN_BAR = """() => { const n = document.querySelector('[data-f-scrollspy]');
  const a = n.querySelector('[aria-current]'); if (!a) return false;
  const l = n.getBoundingClientRect().left + n.clientLeft, r = a.getBoundingClientRect();
  return r.left >= l && r.right <= l + n.clientWidth; }"""


def test_scrollspy_tracks_sections(page_factory, site_url):
    page = page_factory(width=1280)
    page.goto(f"{site_url}/layouts/docs.html")
    page.evaluate("document.querySelector('#config').scrollIntoView()")
    page.wait_for_timeout(200)
    current = page.evaluate(
        "document.querySelector('[data-f-scrollspy] [aria-current]').getAttribute('href')"
    )
    assert current == "#config"
    # The sidebar only marks the link; it never scrolls.
    nav = "document.querySelector('[data-f-scrollspy]')"
    assert page.evaluate(f"[{nav}.scrollLeft, {nav}.scrollTop]") == [0, 0]
    # At the bottom of the page the last section is current, even if it can't reach the line.
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(200)
    assert page.evaluate(
        "[...document.querySelectorAll('[data-f-scrollspy] a')].at(-1).hasAttribute('aria-current')"
    )
    # On a phone the chip bar scrolls itself, never the page, to keep the current link in view.
    page = page_factory(width=390)
    page.goto(f"{site_url}/layouts/docs.html")
    y = page.evaluate("document.querySelector('#config').scrollIntoView(), scrollY")
    page.wait_for_function(CURRENT_IN_BAR, timeout=2000)
    page.wait_for_timeout(600)
    assert page.evaluate(CURRENT_IN_BAR)
    assert page.evaluate(f"{nav}.scrollLeft") > 0
    assert page.evaluate("scrollY") == y


def test_footnote_opens_on_phone(page_factory, site_url):
    page = page_factory(width=390)
    page.goto(f"{site_url}/layouts/margin.html")
    note = page.locator(".f-sidenote").first
    assert not note.is_visible()
    page.locator(".f-sidenote-ref").first.click()
    assert note.is_visible()


def test_footnotes_sit_in_the_margin_on_wide_screens(page_factory, site_url):
    page = page_factory(width=1280)
    page.goto(f"{site_url}/layouts/margin.html")
    note = page.locator(".f-sidenote").first
    assert note.is_visible()
    box = page.evaluate(
        """() => {
            const n = document.querySelector('.f-sidenote').getBoundingClientRect();
            const a = document.querySelector('.f-margin').getBoundingClientRect();
            return {noteLeft: n.left, articleRight: a.right};
        }"""
    )
    assert box["noteLeft"] >= box["articleRight"]


def test_nav_clearance_is_opt_in(page_factory, site_url):
    page = page_factory(width=1280)
    page.goto(f"{site_url}/tests/flow-nav.html")
    assert (
        page.evaluate(
            "getComputedStyle(document.documentElement).getPropertyValue('--f-nav-clear')"
        )
        == "0px"
    )
    pad = page.evaluate(
        "parseFloat(getComputedStyle(document.querySelector('.f-docs')).paddingTop)"
    )
    assert pad < 48


def test_fixed_nav_is_cleared(page_factory, site_url):
    for path, sel in [
        ("docs.html", "h1"),
        ("margin.html", "h1"),
        ("resume.html", ".f-resume__head"),
    ]:
        page = page_factory(width=1280)
        page.goto(f"{site_url}/layouts/{path}")
        nav_bottom = page.evaluate(
            "document.querySelector('.f-nav').getBoundingClientRect().bottom"
        )
        top = page.evaluate(
            f"document.querySelector('main {sel}, article {sel}, .f-docs {sel}')"
            ".getBoundingClientRect().top"
        )
        assert top >= nav_bottom, path
    # The current page's link is a pill inside the pill, not a square.
    radius, height = page.evaluate(
        "(a => [parseFloat(getComputedStyle(a).borderTopLeftRadius), a.offsetHeight])"
        "(document.querySelector('.f-nav a[aria-current]'))"
    )
    assert radius >= height / 2


def test_resume_print_rules_are_scoped(page_factory, site_url):
    page = page_factory(width=1280)
    page.goto(f"{site_url}/components.html")
    page.emulate_media(media="print")
    assert page.evaluate("getComputedStyle(document.querySelector('.f-nav')).display") != "none"
    page = page_factory(width=1280)
    page.goto(f"{site_url}/layouts/resume.html")
    page.emulate_media(media="print")
    assert page.evaluate("getComputedStyle(document.querySelector('.f-nav')).display") == "none"


import pytest  # noqa: E402


def test_nav_turns_glass_after_cover(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/layouts/cover.html")
    nav = page.locator("[data-f-nav-cover]")
    assert "is-scrolled" not in (nav.get_attribute("class") or "")
    page.evaluate("window.scrollTo(0, innerHeight * 1.2)")
    page.wait_for_timeout(300)
    assert "is-scrolled" in nav.get_attribute("class")


@pytest.mark.parametrize("width", [440, 1280])
def test_story_step_matches_image(page_factory, site_url, width):
    page = page_factory(width=width)
    page.goto(f"{site_url}/layouts/story.html")
    steps = page.locator(".f-story__step").count()
    assert steps >= 3
    for i in range(steps):
        page.evaluate(
            f"document.querySelectorAll('.f-story__step')[{i}].scrollIntoView({{block:'center'}})"
        )
        page.wait_for_timeout(250)
        on_step = page.evaluate(
            "[...document.querySelectorAll('.f-story__step')]"
            ".findIndex(s => s.classList.contains('is-on'))"
        )
        on_img = page.evaluate("+document.querySelector('.f-story__stage img.is-on').dataset.step")
        assert on_step == on_img


def test_deck_keys_advance(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/layouts/deck.html")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(900)
    assert page.locator(".f-deck__count").inner_text().startswith("2 /")


@pytest.mark.parametrize("path", ["cover", "story", "panels", "deck", "margin"])
def test_readable_without_js(page_factory, site_url, path):
    from checks import no_hscroll

    page = page_factory(width=390, js=False)
    assert page.goto(f"{site_url}/layouts/{path}.html").ok
    no_hscroll(page)
    hidden = page.evaluate("""[...document.querySelectorAll('main h2, main p')]
      .filter(e => e.textContent.trim() && getComputedStyle(e).visibility === 'hidden'
        || +getComputedStyle(e).opacity === 0).length""")
    assert hidden == 0


@pytest.mark.parametrize("path", ["cover", "story", "panels", "deck", "grid"])
def test_reduced_motion_is_still(page_factory, site_url, path):
    from checks import running_animations

    page = page_factory(reduced_motion=True)
    assert page.goto(f"{site_url}/layouts/{path}.html").ok
    page.wait_for_timeout(500)
    assert running_animations(page) == 0
    if path in ("cover", "panels"):
        assert page.evaluate("[...document.querySelectorAll('video')].every(v => v.paused)")


def test_over_cover_nav_is_readable_without_js(page_factory, site_url):
    from checks import TO_RGB, _lum

    page = page_factory(theme="light", js=False)
    page.goto(f"{site_url}/layouts/cover.html")
    page.evaluate("window.scrollTo(0, innerHeight * 1.2)")
    page.wait_for_timeout(200)
    bg = page.evaluate("getComputedStyle(document.querySelector('.f-nav')).backgroundColor")
    assert bg not in ("transparent", "rgba(0, 0, 0, 0)")
    fg, back = page.evaluate(
        f"""(() => {{
          const f = ({TO_RGB});
          const body = f(getComputedStyle(document.body).backgroundColor);
          const nav = f(getComputedStyle(document.querySelector('.f-nav')).backgroundColor,
            `rgb(${{body.join(' ')}})`);
          const link = document.querySelector('.f-nav a:not([aria-current])');
          return [f(getComputedStyle(link).color, `rgb(${{nav.join(' ')}})`), nav];
        }})()"""
    )
    a, b = sorted([_lum(fg), _lum(back)], reverse=True)
    assert (a + 0.05) / (b + 0.05) >= 4.5


def test_deck_with_bad_data_stays_readable(page_factory, site_url):
    page = page_factory()
    warnings = []
    page.on("console", lambda m: m.type == "warning" and warnings.append(m.text))
    page.goto(f"{site_url}/tests/deck-bad-data.html")
    page.wait_for_timeout(300)
    assert page.errors == []
    assert len(warnings) >= 2
    for deck in ["#bad-from", "#bad-slide"]:
        assert "is-ready" not in page.locator(deck).get_attribute("class")
        shown = page.evaluate(
            f"""[...document.querySelectorAll('{deck} .f-deck__slide :is(h2, p)')]
              .map(e => getComputedStyle(e))
              .every(s => s.visibility !== 'hidden' && +s.opacity > 0 && s.display !== 'none')"""
        )
        assert shown, deck
        assert page.locator(f"{deck} .f-deck__slide h2").count() == 1
    assert "is-ready" in page.locator("#good").get_attribute("class")


def test_resume_prints_in_light_colors_from_the_dark_theme(page_factory, site_url):
    from checks import contrast, contrast_on

    page = page_factory(theme="dark")
    page.goto(f"{site_url}/layouts/resume.html")
    page.emulate_media(media="print")
    for sel in [".f-resume li", ".f-resume dt", ".f-resume__summary", ".f-resume h2"]:
        assert contrast(page, sel) >= 4.5, sel
    assert contrast_on(page, ".f-chip") >= 4.5
    assert page.evaluate("getComputedStyle(document.documentElement).colorScheme") == "light"
    actions = "getComputedStyle(document.querySelector('.f-resume__actions')).display"
    assert page.evaluate(actions) == "none"
    page.emulate_media(media="screen")
    assert page.evaluate(actions) == "flex"


@pytest.mark.parametrize("width", [390, 1280])
def test_page_sidebar_shares_the_docs_grid(page_factory, site_url, width):
    from checks import no_hscroll

    page = page_factory(width=width)
    page.goto(f"{site_url}/tests/page-sidebar.html")
    no_hscroll(page)
    box = page.evaluate("""() => {
      const r = (s) => document.querySelector(s).getBoundingClientRect();
      const main = document.querySelector('main');
      return {toc: r('.f-toc'), art: r('article'), main: r('main'),
              display: getComputedStyle(main).display,
              cols: getComputedStyle(main).gridTemplateColumns};
    }""")
    if width == 1280:
        assert box["display"] == "grid"
        assert box["cols"].split()[0] == "208px"  # the 13rem sidebar track
        assert box["art"]["left"] >= box["toc"]["right"]
        assert abs(box["art"]["top"] - box["toc"]["top"]) < 2
    else:
        assert box["display"] == "block"
        assert box["art"]["top"] >= box["toc"]["bottom"]
        assert box["art"]["width"] > 300


def test_a_wide_child_of_the_sidebar_page_spans_the_row(page_factory, site_url):
    page = page_factory(width=1280)
    page.goto(f"{site_url}/tests/page-sidebar.html")
    wide, toc, art = page.evaluate("""() => ['#wide', '.f-toc', 'article']
      .map((s) => { const r = document.querySelector(s).getBoundingClientRect();
                    return [r.left, r.right]; })""")
    assert wide[0] == pytest.approx(toc[0], abs=1)
    assert wide[1] == pytest.approx(art[1], abs=1)
