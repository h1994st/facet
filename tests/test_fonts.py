import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "src/css/30-fonts.css"


def faces():
    return re.findall(r"@font-face\s*{([^}]*)}", CSS.read_text())


def test_every_face_swaps_and_has_a_file():
    fs = faces()
    assert fs
    for f in fs:
        assert "font-display: swap" in f
        url = re.search(r"url\(\"?fonts/([^\")]+)", f).group(1)
        assert (ROOT / "src/fonts" / url).exists(), url


def test_families_present():
    text = CSS.read_text()
    for fam in ("Geist", "Geist Mono", "Source Serif 4", "Noto Serif SC"):
        assert f'font-family: "{fam}"' in text


def test_cjk_is_sliced():
    sc = [f for f in faces() if '"Noto Serif SC"' in f]
    assert 60 <= len(sc) <= 101  # empty slices are skipped
    assert all("unicode-range" in f for f in sc)


def test_licenses_ship():
    assert len(list((ROOT / "src/fonts").glob("LICENSE-*.txt"))) == 3
