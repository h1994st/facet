"""Search and sharing: what each reference page declares, and what scripts/site_meta.py adds."""

import html
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "scripts"))
import card  # noqa: E402
import site_meta  # noqa: E402

PAGES = sorted(
    p.relative_to(SITE).as_posix() for p in SITE.rglob("*.html") if "tests" not in p.parts
)


def source(rel):
    return (SITE / rel).read_text()


def description(page):
    return html.unescape(
        re.search(r'<meta\s+name="description"\s+content="([^"]*)"', page).group(1)
    )


def test_every_page_has_its_own_title_and_description():
    titles = [
        re.search(r"<title[^>]*>(.*?)</title>", source(p), re.S).group(1).strip() for p in PAGES
    ]
    descs = [description(source(p)) for p in PAGES]
    assert len(set(titles)) == len(PAGES), titles
    assert len(set(descs)) == len(PAGES)
    for rel, desc in zip(PAGES, descs, strict=True):
        assert 50 <= len(desc) <= 160, (rel, len(desc))


@pytest.mark.parametrize("rel", PAGES)
def test_every_page_has_one_h1_and_described_images(rel):
    page = source(rel)
    assert len(re.findall(r"<h1[\s>]", page)) == 1, rel
    for img in re.findall(r"<img\b[^>]*>", page):
        assert re.search(r'\balt="', img), img


@pytest.fixture(scope="module")
def published(tmp_path_factory):
    """The Pages layout that `just site` assembles, decorated by site_meta. dist/ and the assets
    are links to the repo's own, since nothing writes to them."""
    out = tmp_path_factory.mktemp("site")
    shutil.copytree(
        SITE, out, dirs_exist_ok=True, ignore=shutil.ignore_patterns("tests", "dist", "assets")
    )
    (out / "dist").symlink_to(ROOT / "dist")
    (out / "assets").symlink_to(ROOT / "mockups" / "assets")
    shutil.copytree(ROOT / "mockups", out / "mockups", ignore=shutil.ignore_patterns("assets"))
    (out / "mockups" / "assets").symlink_to(ROOT / "mockups" / "assets")
    urls = site_meta.decorate(out)
    (out / "sitemap.xml").write_text(site_meta.sitemap(urls))
    return out


def expected_url(rel, lang="en"):
    prefix = "zh/" if lang == "zh" else ""
    return "https://shengtuo.me/facet/" + prefix + re.sub(r"(^|/)index\.html$", r"\1", rel)


@pytest.mark.parametrize("rel", PAGES)
def test_published_pages_carry_canonical_and_share_tags(published, rel):
    page = (published / rel).read_text()
    # Everything lands inside <head>, once (a page's code samples may quote the same tags).
    head = page[: page.index("</head>")]
    assert page.count('<link rel="canonical"') == 1
    url = expected_url(rel)
    assert f'<link rel="canonical" href="{url}" />' in head
    assert f'<meta property="og:url" content="{url}" />' in head
    assert '<meta property="og:image" content="https://shengtuo.me/facet/card.png" />' in head
    assert '<meta name="twitter:card" content="summary_large_image" />' in head
    assert 'rel="icon"' in head and head.count('name="theme-color"') == 2
    up = "../" * rel.count("/")
    for name in ("geist", "source-serif-4"):
        href = f"{up}dist/fonts/{name}.woff2"
        assert f'<link rel="preload" href="{href}" as="font"' in head
        assert (SITE / rel).parent.joinpath(href).resolve().is_file(), href
    desc = description(source(rel))
    assert f'<meta property="og:description" content="{html.escape(desc)}" />' in head
    ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', head).group(1))
    assert ld["@context"] == "https://schema.org"
    types = {node["@type"] for node in ld["@graph"]}
    assert types == ({"WebSite", "SoftwareSourceCode"} if rel == "index.html" else {"WebPage"})


def test_the_home_page_names_the_released_version(published):
    page = (published / "index.html").read_text()
    ld = json.loads(re.search(r'application/ld\+json">(.*?)</script>', page).group(1))
    code = next(n for n in ld["@graph"] if n["@type"] == "SoftwareSourceCode")
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert code["version"] == version
    assert code["codeRepository"] == "https://github.com/h1994st/facet"


def test_layout_pages_have_breadcrumbs(published):
    page = (published / "layouts/deck.html").read_text()
    ld = json.loads(re.search(r'application/ld\+json">(.*?)</script>', page).group(1))
    crumbs = ld["@graph"][0]["breadcrumb"]["itemListElement"]
    assert [c["name"] for c in crumbs] == ["facet", "Layouts", "Deck layout"]
    assert crumbs[1]["item"] == "https://shengtuo.me/facet/layouts/"


def test_mockups_stay_out_of_search(published):
    for path in (published / "mockups").glob("*.html"):
        page = path.read_text()
        assert '<meta name="robots" content="noindex" />' in page, path.name
        assert 'rel="canonical"' not in page


def test_the_sitemap_lists_every_page_once(published):
    xml = (published / "sitemap.xml").read_text()
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    locs = re.findall(r"<loc>(.*?)</loc>", xml)
    assert sorted(locs) == sorted(expected_url(p, lang) for p in PAGES for lang in ("en", "zh"))
    assert not any("mockups" in u or u.endswith("index.html") for u in locs)


def test_a_page_without_a_description_fails_the_build(tmp_path):
    (tmp_path / "x.html").write_text('<html><head><title data-zh="x">x</title>\n  </head></html>')
    with pytest.raises(SystemExit, match="description"):
        site_meta.decorate(tmp_path)


def test_the_share_card_and_icon_come_from_the_script():
    # The PNG is not compared pixel for pixel: FreeType renders the type differently on macOS and
    # Linux. The icon is plain text, so it must match exactly.
    assert Image.open(SITE / "card.png").size == (1200, 630)
    assert card.draw().size == (1200, 630)
    assert (SITE / "favicon.svg").read_text() == card.icon(), "run `just card`"


def head_of(published, rel, lang):
    page = (published / ("zh/" if lang == "zh" else "") / rel).read_text()
    return page, page[: page.index("</head>")]


@pytest.mark.parametrize("rel", PAGES)
def test_each_language_has_its_own_url_linked_both_ways(published, rel):
    for lang, code in (("en", "en"), ("zh", "zh-Hans")):
        page, head = head_of(published, rel, lang)
        assert f'<html lang="{code}" data-site-lang="{lang}" data-f-ga4="G-ZMH6NLL7C7">' in page
        assert f'<link rel="canonical" href="{expected_url(rel, lang)}" />' in head
        assert f'hreflang="en" href="{expected_url(rel)}"' in head
        assert f'hreflang="zh-Hans" href="{expected_url(rel, "zh")}"' in head
        assert f'hreflang="x-default" href="{expected_url(rel)}"' in head


@pytest.mark.parametrize("rel", PAGES)
def test_the_chinese_copy_has_the_chinese_text_in_place(published, rel):
    en = source(rel)
    zh, head = head_of(published, rel, "zh")
    assert "data-zh=" not in zh
    title_zh = html.unescape(re.search(r'<title data-zh="([^"]*)"', en).group(1))
    assert f"<title>{html.escape(title_zh, quote=False)}</title>" in head or title_zh in head
    h1 = re.search(r'<h1\b[^>]*data-zh="([^"]*)"', en)
    if h1:
        assert html.unescape(h1.group(1)) in zh
    # Code samples (escaped markup) come through unchanged.
    for sample in re.findall(r'<pre class="f-code">(.*?)</pre>', en, re.S):
        assert sample in zh


@pytest.mark.parametrize("rel", PAGES)
def test_every_url_in_the_chinese_copy_resolves(published, rel):
    zh, _ = head_of(published, rel, "zh")
    zh = re.sub(r"<pre\b.*?</pre>", "", zh, flags=re.S)  # code samples quote example URLs
    here = (published / "zh" / rel).parent
    urls = re.findall(r'<[a-zA-Z][^>]*?\b(?:href|src|poster)="([^"]*)"', zh)
    urls += re.findall(r"url\(['\"]?([^)'\"]+)", zh)
    urls += re.findall(r"""\bfrom\s+["'](\.{1,2}/[^"']+)""", zh)
    for url in urls:
        if not url or re.match(r"[a-z]+:|/|#|\?|…", url):
            continue
        path = url.split("#")[0].split("?")[0]
        target = (here / path).resolve()
        if path.endswith("/") or target.is_dir():
            target = target / "index.html"
        assert target.exists(), (rel, url)
        if target.suffix == ".html" and "mockups" not in target.parts:
            assert (published / "zh") in target.parents, (rel, url, "left the Chinese site")


@pytest.fixture(scope="module")
def published_url(published):
    import functools
    import http.server
    import threading

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=str(published))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.mark.parametrize("rel", ["components.html", "layouts/index.html", "cast.html"])
def test_the_chinese_copy_renders_and_switches_by_url(browser, published_url, rel):
    from checks import no_hscroll

    ctx = browser.new_context(viewport={"width": 390, "height": 900})
    page = ctx.new_page()
    page.route(
        "**googletagmanager.com/**",
        lambda r: r.fulfill(body="", content_type="text/javascript"),
    )
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    try:
        page.goto(f"{published_url}/zh/{rel}")
        page.wait_for_selector(".site-bar")
        assert page.evaluate("document.documentElement.lang") == "zh-Hans"
        assert page.evaluate("getComputedStyle(document.body).fontFamily").startswith("Geist")
        assert re.search(r"[一-鿿]", page.inner_text("h1, main"))
        no_hscroll(page)
        current = page.locator(".site-bar a[aria-current]")
        assert "/zh/" in current.get_attribute("href")
        page.click('.site-bar button[data-k="lang"][data-v="en"]')
        page.wait_for_url(f"{published_url}/{rel.removesuffix('index.html')}")
        assert page.evaluate("document.documentElement.lang") == "en"
        page.click('.site-bar button[data-k="lang"][data-v="zh"]')
        page.wait_for_url(f"{published_url}/zh/{rel.removesuffix('index.html')}")
        assert errors == []
    finally:
        ctx.close()


def test_published_pages_carry_the_ga4_id_and_sources_do_not(published):
    for rel in PAGES:
        for prefix in ("", "zh/"):
            page = (published / prefix / rel).read_text()
            assert 'data-f-ga4="G-ZMH6NLL7C7"' in page.split(">", 2)[1] + ">", (prefix, rel)
        # index.html documents the attribute in its text; only the <html> tag matters.
        assert "data-f-ga4" not in re.search(r"<html\b[^>]*>", source(rel)).group(0), rel
    for path in (published / "mockups").glob("*.html"):
        assert "data-f-ga4" not in path.read_text()
