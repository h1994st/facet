"""Fetch the pinned icons into src/icons/ (normalized) with their licenses.

uv run icons/fetch.py

Sources and checksums are in icons/sources.toml. Downloads are cached in icons/.cache/.
"""

import hashlib
import re
import sys
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "icons" / ".cache"
OUT = ROOT / "src" / "icons"
PACKAGES = ("simple-icons", "bootstrap-icons")


def fetch(url: str, sha256: str) -> bytes:
    cached = CACHE / sha256
    if cached.exists():
        data = cached.read_bytes()
    else:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read()
    if hashlib.sha256(data).hexdigest() != sha256:
        cached.unlink(missing_ok=True)
        raise SystemExit(f"checksum mismatch: {url}")
    CACHE.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(data)
    return data


def normalize(svg: str) -> str:
    """One viewBox and the paths' geometry only, so CSS decides size and color."""
    view_box = re.search(r'viewBox="([^"]+)"', svg).group(1)
    paths = []
    for attrs in re.findall(r"<path\b([^>]*?)/?>", svg):
        keep = re.findall(r'\b(d|fill-rule|clip-rule)="([^"]*)"', attrs)
        paths.append("<path " + " ".join(f'{k}="{v}"' for k, v in keep) + "/>")
    if not paths:
        raise SystemExit("an icon without paths")
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}">{"".join(paths)}</svg>\n'


def main() -> None:
    sources = tomllib.loads((ROOT / "icons" / "sources.toml").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    for pkg in PACKAGES:
        base, lic = sources[pkg]["base"], sources[pkg]["license"]
        (OUT / lic["out"]).write_bytes(fetch(base + lic["file"], lic["sha256"]))
        for name, icon in sources[pkg]["icons"].items():
            svg = fetch(base + icon["file"], icon["sha256"]).decode()
            (OUT / f"{name}.svg").write_text(normalize(svg))
    print(f"wrote {len(list(OUT.glob('*.svg')))} icons to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
