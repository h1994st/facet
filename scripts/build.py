"""Build dist/ from src/: concatenate CSS in path order, copy JS, cats and fonts.

uv run scripts/build.py
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(root: Path = ROOT) -> None:
    src, dist = root / "src", root / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir()
    parts = []
    for path in sorted((src / "css").rglob("*.css")):
        rel = path.relative_to(src / "css").as_posix()
        parts.append(f"/* src/css/{rel} */\n{path.read_text().strip()}\n")
    (dist / "facet.css").write_text("\n".join(parts))
    for name in ("js", "cast", "fonts"):
        if (src / name).exists():
            shutil.copytree(src / name, dist / name)


if __name__ == "__main__":
    build()
