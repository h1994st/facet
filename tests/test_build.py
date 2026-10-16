import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
LAYERS = (
    "@layer facet.reset, facet.tokens, facet.base, facet.prose, "
    "facet.cast, facet.components, facet.layouts, facet.utilities;"
)


def build():
    subprocess.run(["uv", "run", "scripts/build.py"], cwd=ROOT, check=True)


def test_layer_order_comes_first():
    build()
    css = (DIST / "facet.css").read_text()
    first_rule = re.sub(r"/\*.*?\*/", "", css, flags=re.S).strip().splitlines()[0]
    assert first_rule == LAYERS


def test_build_is_deterministic():
    build()
    a = (DIST / "facet.css").read_bytes()
    build()
    assert (DIST / "facet.css").read_bytes() == a


def test_every_url_is_relative_and_resolves():
    build()
    css = (DIST / "facet.css").read_text()
    for url in re.findall(r"url\(([^)]+)\)", css):
        url = url.strip("'\"")
        if url.startswith("data:"):
            continue
        assert not url.startswith(("/", "http:", "https:")), url
        target = (DIST / url).resolve()
        assert target.exists(), url
        assert DIST.resolve() in target.parents, url


def test_js_entry_is_copied():
    build()
    assert (DIST / "js" / "facet.js").exists()


def test_backdrop_filter_has_the_webkit_prefix():
    # Safari before 18 only knows -webkit-backdrop-filter; without it the glass goes flat.
    build()
    sources = [DIST / "facet.css", *(ROOT / "site").rglob("*.html")]
    for path in sources:
        if "dist" in path.relative_to(ROOT).parts[1:]:
            continue
        text = path.read_text()
        plain = re.findall(r"(?<![-\w])backdrop-filter:\s*([^;]+);", text)
        prefixed = re.findall(r"-webkit-backdrop-filter:\s*([^;]+);", text)
        assert sorted(plain) == sorted(prefixed), path


def test_pages_site_leaves_out_the_test_fixtures():
    subprocess.run(["just", "site"], cwd=ROOT, check=True, capture_output=True)
    out = ROOT / "_site"
    assert (out / "index.html").exists()
    assert (out / "mockups" / "index.html").exists()
    assert (out / "dist" / "facet.css").exists()
    assert not (out / "tests").exists()


def test_relative_colors_have_a_fallback():
    # A browser without relative colors (oklch(from …)) drops the value. On a normal property
    # that is a parse error, so an earlier declaration of the same property in the rule must
    # carry the fallback. A custom property accepts any value, so there the relative value must
    # sit inside @supports, after a plain declaration.
    build()
    css = re.sub(r"/\*.*?\*/", "", (DIST / "facet.css").read_text(), flags=re.S)
    for m in re.finditer(r"(?<![(\w-])([\w-]+)\s*:\s*[^;{}]*oklch\(from", css):
        prop = m.group(1)
        if prop.startswith("--"):
            opened = css.rfind("@supports", 0, m.start())
            depth = 0
            for ch in css[opened : m.start()]:
                depth += {"{": 1, "}": -1}.get(ch, 0)
            assert opened >= 0 and depth > 0, f"{prop} uses a relative color outside @supports"
        else:
            rule = css[css.rfind("{", 0, m.start()) : m.start()]
            assert re.search(rf"(^|[;{{\s]){re.escape(prop)}\s*:", rule), f"{prop} has no fallback"
