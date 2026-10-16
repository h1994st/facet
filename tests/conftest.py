import functools
import http.server
import json
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parents[1] / "site"


@pytest.fixture(scope="session")
def site_url():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    handler.log_message = lambda *a: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page_factory(browser):
    contexts = []

    def make(width=1280, theme="dark", lang="en", js=True, reduced_motion=False):
        ctx = browser.new_context(
            viewport={"width": width, "height": 900},
            java_script_enabled=js,
            reduced_motion="reduce" if reduced_motion else "no-preference",
        )
        state = json.dumps({"theme": theme, "lang": lang})
        ctx.add_init_script(
            f"try{{localStorage.setItem('facet-site', {json.dumps(state)})}}catch{{}}"
        )
        page = ctx.new_page()
        page.errors = []
        page.on("pageerror", lambda e: page.errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and page.errors.append(m.text))
        contexts.append(ctx)
        return page

    yield make
    for c in contexts:
        c.close()
