"""Make the assembled Pages site (_site/) findable: a Chinese copy of every page, search and sharing
metadata, and a sitemap.

uv run scripts/site_meta.py _site

The reference pages are bilingual in place: an element's data-zh holds its Chinese HTML, and
site.js swaps it in the browser. Search engines index only the HTML a URL serves, so this writes
each page again under zh/ with the Chinese already in place, and links the two with hreflang.

Each page declares only its <title> and <meta name="description"> (each with a data-zh); this adds
the rest from them, so no page repeats it: canonical URL, language alternates, icon, font
preloads, theme-color, Open Graph and Twitter tags, and JSON-LD. Mockups are a decision record,
not documentation, so they get noindex and stay out of the sitemap.
"""

import html
import json
import posixpath
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tokens  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://shengtuo.me/facet/"
REPO = "https://github.com/h1994st/facet"
GA4 = "G-ZMH6NLL7C7"  # shengtuo.me's GA4 property; only published pages carry it
NOINDEX = ("mockups/",)
ZH = "zh/"
LANGS = {"en": ("en", "en_US"), "zh": ("zh-Hans", "zh_CN")}  # hreflang and lang, og:locale
# The fonts every page's first screen uses: Geist for text, Source Serif 4 for the h1.
PRELOAD = ("geist", "source-serif-4")


def url_of(rel: str, lang: str = "en") -> str:
    """The canonical URL of a page: a directory index is served at the directory."""
    return BASE + (ZH if lang == "zh" else "") + re.sub(r"(^|/)index\.html$", r"\1", rel)


def meta_of(page: str, rel: str) -> dict[str, tuple[str, str]]:
    """{lang: (title, description)} from the page's <title> and description, each with a data-zh."""
    title = re.search(r'<title data-zh="([^"]*)">(.*?)</title>', page, re.S)
    desc = re.search(r'<meta\s+name="description"\s+content="([^"]*)"\s+data-zh="([^"]*)"', page)
    if not title or not desc:
        raise SystemExit(
            f"{rel}: every page needs a <title> and a <meta name=description>, each with a data-zh"
        )
    u = html.unescape
    return {
        "en": (u(title.group(2).strip()), u(desc.group(1))),
        "zh": (u(title.group(1)), u(desc.group(2))),
    }


# --- The Chinese copy ----------------------------------------------------------------------------

# A start tag with a data-zh, quoted either way (Prettier single-quotes values holding a ").
DATA_ZH = re.compile(r"""<([a-zA-Z][\w-]*)\b[^>]*?(\s+data-zh=(?:"([^"]*)"|'([^']*)'))[^>]*>""")


def swap_zh(page: str) -> str:
    """Put each element's data-zh in place of its content, as site.js does, and drop the
    attribute. The description <meta> takes it as its content."""
    out, pos = [], 0
    while m := DATA_ZH.search(page, pos):
        tag, attr = m.group(1).lower(), m.group(2)
        zh = html.unescape(m.group(3) if m.group(3) is not None else m.group(4))
        start_tag = m.group(0).replace(attr, "", 1)
        if tag == "meta":
            value = html.escape(zh, quote=True)
            start_tag = re.sub(r'content="[^"]*"', lambda _, v=value: f'content="{v}"', start_tag)
            out += [page[pos : m.start()], start_tag]
            pos = m.end()
            continue
        # The matching end tag: count nested elements with the same name.
        depth = 1
        for t in re.finditer(rf"<(/?){tag}\b[^>]*>", page[m.end() :], re.I):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                end = m.end() + t.start()
                break
        else:
            raise SystemExit(f"no </{tag}> for {m.group(0)[:60]}")
        out += [page[pos : m.start()], start_tag, zh]
        pos = end
    out.append(page[pos:])
    return "".join(out)


def move_url(url: str, rel: str, pages: set[str]) -> str:
    """A relative URL in page rel, rewritten for its zh/ copy: a link to a translated page stays
    inside zh/; anything else (styles, scripts, images, mockups) points back at the shared file."""
    if not url or re.match(r"[a-z][a-z0-9+.-]*:|/|#|\?", url, re.I):
        return url
    path, rest = re.match(r"([^?#]*)(.*)", url).groups()
    here = posixpath.dirname(rel)
    target = posixpath.normpath(posixpath.join(here, path))  # "." is the site root
    is_dir = path.endswith("/") or target == "."
    page = posixpath.join("" if target == "." else target, "index.html") if is_dir else target
    if page in pages:
        return url
    moved = posixpath.relpath(target, posixpath.join("zh", here))
    return moved + ("/" if is_dir else "") + rest


def move_urls(page: str, rel: str, pages: set[str]) -> str:
    """Rewrite every relative URL in real tags, inline styles and module imports. Escaped markup
    in code samples (&lt;…&gt;) is text, so it stays as written."""

    def move(u: str) -> str:
        return move_url(u, rel, pages)

    def in_css(text: str) -> str:
        return re.sub(
            r"url\((['\"]?)([^)'\"]+)\1\)",
            lambda m: f"url({m.group(1)}{move(m.group(2))}{m.group(1)})",
            text,
        )

    def in_tag(m: re.Match) -> str:
        tag = re.sub(
            r'\b(href|src|poster)="([^"]*)"',
            lambda a: f'{a.group(1)}="{move(a.group(2))}"',
            m.group(0),
        )
        return re.sub(r'\bstyle="([^"]*)"', lambda a: f'style="{in_css(a.group(1))}"', tag)

    def in_script(text: str) -> str:
        return re.sub(
            r"""(\bfrom\s+|\bimport\s*\(\s*)(["'])(\.{1,2}/[^"']+)\2""",
            lambda i: f"{i.group(1)}{i.group(2)}{move(i.group(3))}{i.group(2)}",
            text,
        )

    def inside(fix):
        return lambda m: m.group(1) + fix(m.group(2)) + m.group(3)

    page = re.sub(r"<[a-zA-Z][^>]*>", in_tag, page)
    page = re.sub(r"(<style\b[^>]*>)(.*?)(</style>)", inside(in_css), page, flags=re.S)
    return re.sub(r"(<script\b[^>]*>)(.*?)(</script>)", inside(in_script), page, flags=re.S)


def set_lang(page: str, lang: str) -> str:
    """Mark the page's language for search, and for site.js, which then switches by URL; and turn
    on analytics, which only the published pages carry."""
    return re.sub(
        r"<html\b[^>]*>",
        f'<html lang="{LANGS[lang][0]}" data-site-lang="{lang}" data-f-ga4="{GA4}">',
        page,
        count=1,
    )


# --- Metadata ------------------------------------------------------------------------------------


def schema(rel: str, lang: str, meta: dict, version: str) -> dict:
    title, desc = meta[lang]
    site = {"@id": BASE + "#website"}
    url = url_of(rel, lang)
    if rel == "index.html":
        graph = [
            {
                "@type": "WebSite",
                **site,
                "url": BASE,
                "name": "facet",
                "description": meta["en"][1],
                "inLanguage": [LANGS["en"][0], LANGS["zh"][0]],
            },
            {
                "@type": "SoftwareSourceCode",
                "name": "facet",
                "description": desc,
                "url": url,
                "inLanguage": LANGS[lang][0],
                "codeRepository": REPO,
                "license": "https://opensource.org/licenses/MIT",
                "programmingLanguage": ["CSS", "JavaScript"],
                "version": version,
            },
        ]
    else:
        crumbs = [("facet", url_of("index.html", lang))]
        if rel.startswith("layouts/") and rel != "layouts/index.html":
            name = "版式" if lang == "zh" else "Layouts"
            crumbs.append((name, url_of("layouts/index.html", lang)))
        crumbs.append((title.split(" · ")[0], url))
        graph = [
            {
                "@type": "WebPage",
                "@id": url,
                "url": url,
                "name": title,
                "description": desc,
                "inLanguage": LANGS[lang][0],
                "isPartOf": site,
                "breadcrumb": {
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": i, "name": name, "item": item}
                        for i, (name, item) in enumerate(crumbs, 1)
                    ],
                },
            }
        ]
    return {"@context": "https://schema.org", "@graph": graph}


def head_tags(rel: str, lang: str, meta: dict, version: str) -> str:
    title, desc = meta[lang]
    up = "../" * (rel.count("/") + (lang == "zh"))
    dark, light = (tokens.hex_color(c) for c in tokens.token("bg"))
    other = "en" if lang == "zh" else "zh"
    attr = lambda s: html.escape(s, quote=True)  # noqa: E731
    ld = json.dumps(schema(rel, lang, meta, version), ensure_ascii=False).replace("</", "<\\/")
    tags = [
        f'<link rel="canonical" href="{url_of(rel, lang)}" />',
        *(
            f'<link rel="alternate" hreflang="{LANGS[x][0]}" href="{url_of(rel, x)}" />'
            for x in ("en", "zh")
        ),
        f'<link rel="alternate" hreflang="x-default" href="{url_of(rel)}" />',
        f'<link rel="icon" href="{up}favicon.svg" type="image/svg+xml" />',
        *(
            f'<link rel="preload" href="{up}dist/fonts/{name}.woff2" as="font" type="font/woff2"'
            " crossorigin />"
            for name in PRELOAD
        ),
        f'<meta name="theme-color" media="(prefers-color-scheme: dark)" content="{dark}" />',
        f'<meta name="theme-color" media="(prefers-color-scheme: light)" content="{light}" />',
        '<meta property="og:type" content="website" />',
        '<meta property="og:site_name" content="facet" />',
        f'<meta property="og:locale" content="{LANGS[lang][1]}" />',
        f'<meta property="og:locale:alternate" content="{LANGS[other][1]}" />',
        f'<meta property="og:title" content="{attr(title)}" />',
        f'<meta property="og:description" content="{attr(desc)}" />',
        f'<meta property="og:url" content="{url_of(rel, lang)}" />',
        f'<meta property="og:image" content="{BASE}card.png" />',
        '<meta property="og:image:width" content="1200" />',
        '<meta property="og:image:height" content="630" />',
        '<meta property="og:image:alt" content="facet: a shared design language for a family of '
        'websites, with its thirteen accent colors" />',
        '<meta name="twitter:card" content="summary_large_image" />',
        f'<script type="application/ld+json">{ld}</script>',
    ]
    return "".join(f"    {t}\n" for t in tags)


def add_head(page: str, rel: str, tags: str) -> str:
    """Insert tags on the line before </head>, so the output keeps the page's indentation."""
    if "</head>" not in page:
        raise SystemExit(f"{rel}: no </head>")
    end = page.index("</head>")
    start = page.rindex("\n", 0, end) + 1
    return page[:start] + tags + page[start:]


def decorate(site: Path) -> list[str]:
    """Write the zh/ copies and add the metadata to every page under site/ in place; return the
    indexed pages' URLs."""
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    rels = sorted(p.relative_to(site).as_posix() for p in site.rglob("*.html"))
    pages = {r for r in rels if not r.startswith((*NOINDEX, ZH))}
    urls = []
    for rel in rels:
        path = site / rel
        page = path.read_text()
        if rel.startswith(NOINDEX):
            path.write_text(add_head(page, rel, '    <meta name="robots" content="noindex" />\n'))
        if rel not in pages:
            continue
        meta = meta_of(page, rel)
        zh = set_lang(move_urls(swap_zh(page), rel, pages), "zh")
        out = site / ZH / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(add_head(zh, rel, head_tags(rel, "zh", meta, version)))
        path.write_text(add_head(set_lang(page, "en"), rel, head_tags(rel, "en", meta, version)))
        urls += [url_of(rel), url_of(rel, "zh")]
    return urls


def sitemap(urls: list[str]) -> str:
    rows = "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{rows}</urlset>\n"
    )


if __name__ == "__main__":
    site = Path(sys.argv[1])
    (site / "sitemap.xml").write_text(sitemap(decorate(site)))
