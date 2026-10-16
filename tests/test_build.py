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
