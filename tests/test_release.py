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


def test_pinned_versions_follow_releases():
    # release-please rewrites only the first version on each line between its markers, so each
    # line holds at most one, and every one is the current release.
    manifest = json.loads((ROOT / ".release-please-manifest.json").read_text())["."]
    for path in ["README.md", "site/index.html"]:
        blocks = re.findall(
            r"x-release-please-start-version -->(.*?)<!-- x-release-please-end",
            (ROOT / path).read_text(),
            re.S,
        )
        assert blocks, path
        for line in "".join(blocks).splitlines():
            versions = re.findall(r"\d+\.\d+\.\d+", line)
            assert len(versions) <= 1 and set(versions) <= {manifest}, (path, line)
