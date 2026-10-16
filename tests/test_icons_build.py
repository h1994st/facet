"""The icon set: normalized sources in src/icons/, and dist/icons.css generated from them."""

import re
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "icons"
DIST = ROOT / "dist"
SOURCES = tomllib.loads((ROOT / "icons" / "sources.toml").read_text())
NAMES = sorted(n for pkg in ("simple-icons", "bootstrap-icons") for n in SOURCES[pkg]["icons"])


def build():
    subprocess.run(["uv", "run", "scripts/build.py"], cwd=ROOT, check=True)


def test_the_set_is_the_nineteen_icons():
    assert len(NAMES) == 19
    assert sorted(p.stem for p in SRC.glob("*.svg")) == NAMES


def test_sources_are_normalized():
    for path in SRC.glob("*.svg"):
        svg = path.read_text()
        assert re.fullmatch(
            r'<svg xmlns="http://www.w3.org/2000/svg" viewBox="[\d. ]+">(<path [^>]*/>)+</svg>\n',
            svg,
        ), path.name
        assert not re.search(r"\b(fill|width|height|class|role)=|<title", svg), path.name


def test_icons_css_has_one_rule_per_icon_and_the_alias():
    build()
    css = (DIST / "icons.css").read_text()
    assert "@layer facet.components" in css
    # Declares facet's layer order first, so loading it before facet.css changes nothing.
    layers = (ROOT / "src" / "css" / "00-layers.css").read_text().strip()
    facet = re.sub(r"/\*.*?\*/", "", (DIST / "facet.css").read_text(), flags=re.S).strip()
    assert facet.startswith(layers)
    assert re.sub(r"/\*.*?\*/", "", css, flags=re.S).strip().startswith(layers)
    rules = dict(re.findall(r'\.f-icon--([a-z-]+)[^{]*\{\s*--f-icon: url\("([^"]+)"\)', css))
    assert sorted(rules) == NAMES
    for name, uri in rules.items():
        assert uri.startswith("data:image/svg+xml,")
        assert unquote(uri.removeprefix("data:image/svg+xml,")) == (SRC / f"{name}.svg").read_text()
    assert re.search(r"\.f-icon--twitter,\s*\.f-icon--x\b|\.f-icon--x,\s*\.f-icon--twitter\b", css)


def test_dist_ships_the_files_and_licenses():
    build()
    for name in NAMES:
        assert (DIST / "icons" / f"{name}.svg").read_text() == (SRC / f"{name}.svg").read_text()
    assert (DIST / "icons" / "LICENSE-simple-icons.md").read_text().startswith("# CC0")
    assert "MIT" in (DIST / "icons" / "LICENSE-bootstrap-icons.txt").read_text()
