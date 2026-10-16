"""Analytics: GA4 loads once from <html data-f-ga4>, and only then."""

GTAG = "**googletagmanager.com/gtag/js*"
FACET = "import('/dist/js/facet.js')"


def stub(page, requests, abort=False):
    def handle(route):
        requests.append(route.request.url)
        if abort:
            route.abort()
        else:
            route.fulfill(body="", content_type="text/javascript")

    page.route(GTAG, handle)


def layer(page):
    return page.evaluate("JSON.parse(JSON.stringify((window.dataLayer || []).map(a => [...a])))")


def open_fixture(page_factory, site_url, **kw):
    page = page_factory(**kw)
    requests = []
    stub(page, requests)
    page.goto(f"{site_url}/tests/analytics.html")
    page.wait_for_function("window.dataLayer && window.dataLayer.length >= 2")
    return page, requests


def test_loads_gtag_once_and_configures_once(page_factory, site_url):
    page, requests = open_fixture(page_factory, site_url)
    assert len(requests) == 1 and "id=G-TEST123" in requests[0]
    configs = [e for e in layer(page) if e[0] == "config"]
    assert configs == [["config", "G-TEST123"]]
    assert not any(e[:2] == ["event", "page_view"] for e in layer(page))


def test_init_twice_adds_nothing(page_factory, site_url):
    page, requests = open_fixture(page_factory, site_url)
    page.evaluate(f"{FACET}.then((m) => {{ m.init(); m.init(); }})")
    assert page.locator('script[src*="googletagmanager"]').count() == 1
    assert len([e for e in layer(page) if e[0] == "config"]) == 1
    page.click("#out")
    assert len([e for e in layer(page) if e[:2] == ["event", "outbound_demo"]]) == 1


def test_event_on_a_child_click(page_factory, site_url):
    page, _ = open_fixture(page_factory, site_url)
    page.click("#inner")
    event = [e for e in layer(page) if e[:2] == ["event", "outbound_demo"]][0]
    assert event[2]["label"] == "demo"
    assert event[2]["link_url"].endswith("/tests/analytics.html#out")


def test_bad_event_name_warns_and_sends_nothing(page_factory, site_url):
    page, _ = open_fixture(page_factory, site_url)
    warnings = []
    page.on("console", lambda m: m.type == "warning" and warnings.append(m.text))
    page.click("#badname")
    assert not any(e[:2] == ["event", "Bad Name"] for e in layer(page))
    assert any("data-f-event" in w for w in warnings)


def test_theme_switch_is_reported(page_factory, site_url):
    page, _ = open_fixture(page_factory, site_url)
    page.click("[data-f-theme-toggle]")
    assert ["event", "theme_change", {"theme": "light"}] in layer(page)


def test_global_privacy_control_turns_it_off(page_factory, site_url):
    page = page_factory()
    requests = []
    stub(page, requests)
    page.add_init_script(
        "Object.defineProperty(navigator, 'globalPrivacyControl', {get: () => true})"
    )
    page.goto(f"{site_url}/tests/analytics.html")
    page.wait_for_load_state("load")
    page.wait_for_timeout(200)
    assert requests == []
    assert layer(page) == []


def test_nothing_without_a_valid_id(page_factory, site_url):
    page = page_factory()
    requests = []
    stub(page, requests)
    page.goto(f"{site_url}/components.html")
    page.evaluate(
        "import('/dist/js/analytics.js').then((m) => {"
        " document.documentElement.dataset.fGa4 = 'bogus'; m.init(); })"
    )
    page.wait_for_timeout(200)
    assert requests == []
    assert page.locator('script[src*="googletagmanager"]').count() == 0


def test_blocked_gtag_breaks_nothing_else(page_factory, site_url):
    page = page_factory()
    requests = []
    stub(page, requests, abort=True)
    page.goto(f"{site_url}/tests/analytics.html")
    page.wait_for_function("window.dataLayer && window.dataLayer.length >= 2")
    page.click("[data-f-theme-toggle]")
    assert page.evaluate("document.documentElement.dataset.theme") == "light"
    assert all("Failed to load resource" in e or "ERR_FAILED" in e for e in page.errors)
    page.errors.clear()
