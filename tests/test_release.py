import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def config():
    return json.loads((ROOT / "release-please-config.json").read_text())["packages"]["."]


def test_tags_are_plain_versions():
    # The docs pin `@v0.1.0`; release-please's default would tag `facet-v0.1.0`.
    assert config()["include-component-in-tag"] is False


def test_pyproject_version_follows_releases():
    paths = [f["path"] for f in config()["extra-files"]]
    assert "pyproject.toml" in paths
    text = (ROOT / "pyproject.toml").read_text()
    assert re.search(r'^version = "[^"]+" # x-release-please-version$', text, re.M)
    version = tomllib.loads(text)["project"]["version"]
    manifest = json.loads((ROOT / ".release-please-manifest.json").read_text())["."]
    expected = config()["initial-version"] if manifest == "0.0.0" else manifest
    assert version == expected
