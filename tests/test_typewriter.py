"""Typewriter: types phrases into an element, and stays still when it should."""

FACET = "import('/dist/js/facet.js')"


def text(page, sel="#t"):
    return page.evaluate(f"document.querySelector({sel!r}).textContent")


def install_paused_clock(page):
    # A clock that is only installed keeps moving in real time, so a slow start would fire the
    # timers early. Paused, it moves only with run_for.
    page.clock.install(time=0)
    page.clock.pause_at(1000)


def frame(page):
    # A paused clock also stops requestAnimationFrame, so wait for a rendered frame through an
    # observer of our own: intersection observers report together, after the page's own.
    page.evaluate(
        "new Promise((r) => { const io = new IntersectionObserver(() => { io.disconnect(); r(); });"
        " io.observe(document.body); })"
    )
    page.clock.run_for(32)


def ready(page_factory, site_url, **kw):
    page = page_factory(**kw)
    install_paused_clock(page)
    page.goto(f"{site_url}/tests/typewriter.html")
    page.wait_for_function("document.querySelector('#t').dataset.fTypeOn === '1'")
    return page


def test_types_each_phrase_after_the_shown_one(page_factory, site_url):
    page = ready(page_factory, site_url)
    assert text(page) == "meow"
    page.clock.run_for(2500)
    assert text(page) == ""
    page.clock.run_for(50)
    assert text(page) == "h"
    page.clock.run_for(50)
    assert text(page) == "hi"
    page.clock.run_for(2499)
    assert text(page) == "hi"


def test_types_whole_graphemes(page_factory, site_url):
    page = ready(page_factory, site_url)
    page.clock.run_for(2500 + 100 + 2500)
    seen = []
    for _ in range(3):
        page.clock.run_for(50)
        seen.append(text(page))
    assert seen[:2] == ["喵", "喵🐾"]


def test_loops_back_to_the_first_phrase(page_factory, site_url):
    page = ready(page_factory, site_url)
    # meow is shown; then hi, 喵🐾, and meow again.
    page.clock.run_for(2500 + 100 + 2500 + 100 + 2500 + 200)
    assert text(page) == "meow"


def test_still_under_reduced_motion(page_factory, site_url):
    page = page_factory(reduced_motion=True)
    install_paused_clock(page)
    page.goto(f"{site_url}/tests/typewriter.html")
    # In view, and a frame rendered: an observer that was wrongly running would have fired by now.
    page.wait_for_function("document.querySelector('#t').getBoundingClientRect().bottom > 0")
    frame(page)
    # Sample mid-cycle: a moving loop shows "", "h" or "hi" here, never "meow".
    for ms in (2550, 2600, 2500):
        page.clock.run_for(ms)
        assert text(page) == "meow"
    assert page.evaluate("document.querySelector('#t').dataset.fTypeOn") is None


def test_bad_data_warns_and_leaves_the_text(page_factory, site_url):
    page = page_factory()
    warnings = []
    page.on("console", lambda m: m.type == "warning" and warnings.append(m.text))
    page.goto(f"{site_url}/tests/typewriter.html")
    page.wait_for_function("document.querySelector('#t').dataset.fTypeOn === '1'")
    assert text(page, "#bad") == "still"
    assert any("data-f-type" in w for w in warnings)


def test_waits_while_off_screen(page_factory, site_url):
    page = ready(page_factory, site_url)
    page.clock.run_for(10000)
    assert text(page, "#far") == "a"
    page.evaluate("document.querySelector('#far').scrollIntoView()")
    page.wait_for_function("document.querySelector('#far').dataset.fTypeOn === '1'")
    page.clock.run_for(2600)
    assert text(page, "#far") in ("", "b")


def test_waits_while_the_tab_is_hidden(page_factory, site_url):
    page = ready(page_factory, site_url)
    page.evaluate(
        "Object.defineProperty(document, 'hidden', {value: true, configurable: true});"
        "document.dispatchEvent(new Event('visibilitychange'))"
    )
    page.clock.run_for(2550)
    assert text(page) == "meow"
    page.clock.run_for(10000)
    assert text(page) == "meow"
    page.evaluate(
        "Object.defineProperty(document, 'hidden', {value: false, configurable: true});"
        "document.dispatchEvent(new Event('visibilitychange'))"
    )
    page.clock.run_for(2500)
    assert text(page) == ""


def test_init_twice_runs_one_loop_and_cleanup_restores(page_factory, site_url):
    page = ready(page_factory, site_url)
    page.evaluate(f"{FACET}.then((m) => m.init())")
    page.clock.run_for(2550)
    assert text(page) == "h"
    page.evaluate(f"{FACET}.then((m) => m.cleanup())")
    assert text(page) == "meow"
    assert page.evaluate("document.querySelector('#t').dataset.fTypeOn") is None


def test_cleanup_then_observer_activity_stays_still(page_factory, site_url):
    page = ready(page_factory, site_url)
    page.evaluate(f"{FACET}.then((m) => m.cleanup())")
    # Off screen and back, a frame each, so a still-connected observer would report both.
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    frame(page)
    page.evaluate("window.scrollTo(0, 0)")
    frame(page)
    page.clock.run_for(6000)
    assert text(page) == "meow"
    assert page.evaluate("document.querySelector('#t').dataset.fTypeOn") is None


def test_text_that_is_not_a_phrase_holds_then_starts_at_the_first(page_factory, site_url):
    page = ready(page_factory, site_url)
    page.wait_for_function("document.querySelector('#other').dataset.fTypeOn === '1'")
    assert text(page, "#other") == "z"
    page.clock.run_for(2499)
    assert text(page, "#other") == "z"
    page.clock.run_for(1)
    assert text(page, "#other") == ""
    page.clock.run_for(50)
    assert text(page, "#other") == "x"
