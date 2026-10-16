"""Figure, gallery and variants: the screenshot grids and diagram figures of a blog post."""

import pytest
from checks import contrast, no_hscroll

FACET = "import('/dist/js/facet.js')"
IMG = "../assets/board-1.jpg"


def put(page, site_url, body):
    page.goto(f"{site_url}/tests/variants.html")
    page.evaluate("b => { document.body.innerHTML = b }", body)


FIGURE = f"""
<main class="f-prose" style="max-width: 40rem; margin: 2rem auto">
  <figure class="f-figure" id="plain">
    <p class="f-figure__kicker">Diagram</p>
    <img src="{IMG}" alt="" width="1280" height="800" />
    <figcaption><b>Steer.</b> Mirrors mix the light.</figcaption>
  </figure>
  <figure class="f-figure f-figure--bare" id="bare">
    <img src="{IMG}" alt="" width="1280" height="800" />
  </figure>
</main>
"""


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_figure_caption_and_contrast(page_factory, site_url, theme):
    page = page_factory(theme=theme)
    put(page, site_url, FIGURE)
    page.wait_for_load_state("load")
    b = page.evaluate(
        "(() => { const s = getComputedStyle(document.querySelector('.f-figure b'));"
        " const fg = getComputedStyle(document.querySelector('.f-figure b')).color;"
        " const body = getComputedStyle(document.body).color;"
        " return [s.fontWeight, fg === body]; })()"
    )
    assert b == ["600", True]
    assert contrast(page, ".f-figure__kicker") >= 4.5
    assert contrast(page, ".f-figure figcaption") >= 4.5


def test_figure_bare_drops_the_frame(page_factory, site_url):
    page = page_factory()
    put(page, site_url, FIGURE)
    style = (
        "(sel) => { const s = getComputedStyle(document.querySelector(sel));"
        " return [s.boxShadow, s.borderTopLeftRadius]; }"
    )
    shadow, radius = page.evaluate(style, "#plain img")
    assert shadow != "none" and radius != "0px"
    assert page.evaluate(style, "#bare img") == ["none", "0px"]


GALLERY = f"""
<ul class="f-gallery">
  <li><img src="{IMG}" alt="" width="1280" height="800" />
  <span class="f-gallery__label">One</span></li>
  <li><img src="{IMG}" alt="" width="1280" height="800" />
  <span class="f-gallery__label">Two</span></li>
  <li><img src="{IMG}" alt="" width="1280" height="800" />
  <span class="f-gallery__label">Three</span></li>
</ul>
"""

TOPS = (
    "[...document.querySelectorAll('.f-gallery > li')]"
    ".map(e => Math.round(e.getBoundingClientRect().top))"
)


def test_gallery_columns(page_factory, site_url):
    wide = page_factory(width=1280)
    put(wide, site_url, GALLERY)
    tops = wide.evaluate(TOPS)
    assert tops[0] == tops[1], "two columns at 1280"
    narrow = page_factory(width=390)
    put(narrow, site_url, GALLERY)
    tops = narrow.evaluate(TOPS)
    assert tops[0] < tops[1] < tops[2], "one column at 390"
    no_hscroll(narrow)
    assert narrow.locator(".f-gallery__label").count() == 3
    assert (
        narrow.evaluate("getComputedStyle(document.querySelector('.f-gallery__label')).fontFamily")
        .lower()
        .count("mono")
    )


def shown(page, sel):
    return page.evaluate(f"!document.querySelector({sel!r}).hidden")


def test_variants_without_js(page_factory, site_url):
    page = page_factory(js=False)
    page.goto(f"{site_url}/tests/variants.html")
    assert not page.locator("[data-f-variants]").first.is_visible()
    assert page.locator("#a-modern").is_visible()
    assert not page.locator("#a-classic").is_visible()


def test_variants_switch_within_scope(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/tests/variants.html")
    page.wait_for_function("!document.querySelector('[data-f-variants]').hidden")
    assert page.locator("#a [data-f-variants]").is_visible()
    # The size group has no pressed button: its first variant shows.
    assert shown(page, "#b-small") and not shown(page, "#b-large")
    page.click("#a button[data-variant=classic]")
    assert shown(page, "#a-classic") and not shown(page, "#a-modern")
    assert page.get_attribute("#a button[data-variant=classic]", "aria-pressed") == "true"
    assert page.get_attribute("#a button[data-variant=modern]", "aria-pressed") == "false"
    # Other groups, and the same group elsewhere in the page, are untouched.
    assert shown(page, "#b-small") and not shown(page, "#b-large")
    assert shown(page, "#b-look")
    page.click("#b button[data-variant=large]")
    assert shown(page, "#b-large") and not shown(page, "#b-small")
    assert shown(page, "#a-classic")


COUNT = """() => { window.__writes = 0; if (window.__wrapped) return; window.__wrapped = 1;
  const b = document.querySelector('#a button[data-variant=classic]');
  const set = b.setAttribute.bind(b);
  b.setAttribute = (n, v) => { if (n === 'aria-pressed') window.__writes++; set(n, v); }; }"""


def test_variants_init_twice_binds_once(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/tests/variants.html")
    page.wait_for_function("!document.querySelector('[data-f-variants]').hidden")
    page.evaluate(
        "import('/dist/js/variants.js').then(m => { window.__m = m; m.init(); m.init(); })"
    )
    page.wait_for_function("window.__m")
    page.evaluate(COUNT)
    page.click("#a button[data-variant=classic]")
    assert page.evaluate("window.__writes") == 1
    assert shown(page, "#a-classic") and not shown(page, "#a-modern")
    # Cleanup then init binds again, once.
    page.evaluate(
        "import('/dist/js/facet.js').then(m => { m.cleanup(); window.__m.init(); window.__r = 1; })"
    )
    page.wait_for_function("window.__r")
    page.evaluate(COUNT)
    page.click("#a button[data-variant=classic]")
    assert page.evaluate("window.__writes") == 1
    page.evaluate("document.querySelector('#a button[data-variant=modern]').click()")
    assert shown(page, "#a-modern")


def test_variant_group_names_are_exact(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/tests/variants.html")
    page.wait_for_function("!document.querySelector('[data-f-variants]').hidden")
    page.click("#c button[data-variant=y]")
    assert shown(page, "#c-ay") and not shown(page, "#c-ax")
    assert shown(page, "#c-abp") and not shown(page, "#c-abq")
    page.click("#c button[data-variant=q]")
    assert shown(page, "#c-abq") and not shown(page, "#c-abp")
    assert shown(page, "#c-ay"), "group a is untouched by a:b"
    assert not shown(page, "#c-orphan"), "a value with no button stays hidden"


def test_variants_control_without_buttons_stays_hidden(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/tests/variants.html")
    page.wait_for_function("!document.querySelector('[data-f-variants]').hidden")
    assert page.evaluate("document.querySelector('#d [data-f-variants]').hidden")


def test_gallery_min_never_overflows(page_factory, site_url):
    page = page_factory(width=390)
    put(
        page,
        site_url,
        GALLERY.replace('class="f-gallery"', 'class="f-gallery" style="--f-gallery-min: 30rem"'),
    )
    tops = page.evaluate(TOPS)
    assert tops[0] < tops[1] < tops[2]
    no_hscroll(page)


def test_variants_cleanup_restores(page_factory, site_url):
    page = page_factory()
    page.goto(f"{site_url}/tests/variants.html")
    page.wait_for_function("!document.querySelector('[data-f-variants]').hidden")
    page.click("#a button[data-variant=classic]")
    page.evaluate("import('/dist/js/facet.js').then(m => { m.cleanup(); window.__done = 1; })")
    page.wait_for_function("window.__done")
    assert page.evaluate("document.querySelector('#a [data-f-variants]').hidden")
    assert shown(page, "#a-modern") and not shown(page, "#a-classic")
    assert not shown(page, "#b-large") and shown(page, "#b-small") and shown(page, "#b-look")
    assert page.evaluate("document.querySelector('#b [data-f-variants]').hidden")
    page.evaluate("document.querySelector('#a button[data-variant=classic]').click()")
    assert shown(page, "#a-modern"), "listeners are gone"
