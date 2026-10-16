#!/usr/bin/env python3
"""Draw the text-free demo images for the layout mockups, in facet's muted palette.

    uv run --with pillow mockups/assets/craft.py

Writes aurora.jpg, prism.jpg, horizon.jpg and mist.jpg (1920x1080), board.jpg (a laser-puzzle
board, 1920x1080), board-1..4.jpg (smaller boards, 1280x800) and, when ffmpeg is installed, loop.mp4
and loop-poster.jpg (an 8-second muted video loop) next to this script. Output is deterministic
(seeded), so rerunning reproduces the same files.
"""
import math
import random
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

W, H = 1920, 1080
OUT = Path(__file__).resolve().parent
random.seed(7)

# Muted accents (OKLCH L~0.7, C~0.07), as sRGB.
MOSS = (150, 172, 118)
SLATE = (126, 150, 196)
SAGE = (122, 176, 152)
ROSE = (206, 138, 146)
OCHRE = (196, 168, 112)
LAVENDER = (164, 146, 200)
NIGHT = (11, 13, 20)


def glow(size, xy, radius, color, strength=1.0, blur=None):
    """A soft colored blob on black, for adding with ImageChops.add."""
    layer = Image.new("RGB", size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    c = tuple(int(v * strength) for v in color)
    d.ellipse([x - radius, y - radius, x + radius, y + radius], fill=c)
    return layer.filter(ImageFilter.GaussianBlur(blur or radius * 0.6))


def grain(img, amount=6):
    noise = Image.effect_noise(img.size, 40).convert("RGB")
    return Image.blend(img, ImageChops.add(img, noise, scale=1.0, offset=-128), amount / 100)


def save(img, name):
    img.save(OUT / name, quality=84, optimize=True, progressive=True)
    print("wrote", name)


def aurora():
    img = Image.new("RGB", (W, H), NIGHT)
    for xy, r, c, s in [
        ((380, 820), 420, MOSS, 0.32),
        ((1300, 300), 440, SLATE, 0.3),
        ((1720, 940), 320, LAVENDER, 0.24),
        ((960, 1080), 300, SAGE, 0.18),
    ]:
        img = ImageChops.add(img, glow((W, H), xy, r, c, s))
    return grain(img)


def prism():
    img = Image.new("RGB", (W, H), NIGHT)
    cx, cy = 900, 560
    tri = [(cx, cy - 230), (cx - 210, cy + 150), (cx + 210, cy + 150)]
    # Incoming white beam.
    beams = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(beams)
    d.line([(0, cy + 70), (cx - 105, cy - 10)], fill=(225, 228, 238), width=6)
    # Outgoing fan, muted.
    for i, c in enumerate([ROSE, OCHRE, MOSS, SAGE, SLATE, LAVENDER]):
        a = math.radians(-14 + i * 6.5)
        x0, y0 = cx + 100, cy + 10
        d.line([(x0, y0), (x0 + 1400 * math.cos(a), y0 + 1400 * math.sin(a))], fill=c, width=7)
    img = ImageChops.add(img, beams.filter(ImageFilter.GaussianBlur(18)))
    img = ImageChops.add(img, beams.filter(ImageFilter.GaussianBlur(3)))
    # The glass: faint fill, bright edges, a soft inner reflection.
    glass = Image.new("RGB", (W, H), (0, 0, 0))
    g = ImageDraw.Draw(glass)
    g.polygon(tri, fill=(26, 30, 42))
    img = ImageChops.add(img, glass)
    edges = Image.new("RGB", (W, H), (0, 0, 0))
    e = ImageDraw.Draw(edges)
    e.line(tri + [tri[0]], fill=(200, 208, 228), width=3, joint="curve")
    img = ImageChops.add(img, edges.filter(ImageFilter.GaussianBlur(1)))
    img = ImageChops.add(img, edges.filter(ImageFilter.GaussianBlur(10)))
    img = ImageChops.add(img, glow((W, H), (cx - 40, cy - 40), 120, (90, 96, 120), 0.6))
    img = ImageChops.add(img, glow((W, H), (cx + 120, cy + 10), 160, (120, 110, 90), 0.5))
    return grain(img)


def horizon():
    img = Image.new("RGB", (W, H), NIGHT)
    hy = int(H * 0.5)
    lines = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(lines)
    vx = W // 2
    for i in range(-24, 25):
        x = vx + i * 160
        d.line([(vx + i * 6, hy), (x * 1 + (x - vx) * 2, H)], fill=(70, 86, 120), width=2)
    for k in range(1, 18):
        t = (k / 18) ** 2.2
        y = hy + t * (H - hy)
        d.line([(0, y), (W, y)], fill=(70, 86, 120), width=2)
    mask = Image.linear_gradient("L").resize((W, H))  # dark at top, bright at bottom
    lines = Image.composite(lines, Image.new("RGB", (W, H)), mask)
    img = ImageChops.add(img, lines)
    img = ImageChops.add(img, glow((W, H), (vx, hy), 520, SLATE, 0.55, blur=260))
    img = ImageChops.add(img, glow((W, H), (vx, hy - 40), 220, ROSE, 0.35, blur=140))
    sky = Image.new("RGB", (W, H), (0, 0, 0))
    s = ImageDraw.Draw(sky)
    for _ in range(140):
        x, y = random.randrange(W), random.randrange(hy - 40)
        v = random.randint(60, 150)
        s.point((x, y), fill=(v, v, v + 20))
    img = ImageChops.add(img, sky)
    return grain(img)


def mist():
    """A light-theme field: pale cool gray with soft color washes."""
    img = Image.new("RGB", (W, H), (240, 242, 246))
    for xy, r, c in [
        ((380, 300), 560, (214, 226, 210)),
        ((1500, 260), 520, (214, 220, 238)),
        ((1100, 900), 600, (236, 220, 222)),
    ]:
        layer = Image.new("RGB", (W, H), (240, 242, 246))
        ImageDraw.Draw(layer).ellipse([xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r], fill=c)
        img = ImageChops.darker(img, layer.filter(ImageFilter.GaussianBlur(r * 0.55)))
    return grain(img, 3)


def board(seed, size=(W, H), cols=12, rows=7):
    """A laser-puzzle board: glass tiles on a grid, emitters, and muted beams that bend at
    mirrors and end in lit targets."""
    rnd = random.Random(seed)
    w, h = size
    cell = min(w / (cols + 2), h / (rows + 2))
    ox, oy = (w - cell * cols) / 2, (h - cell * rows) / 2
    img = Image.new("RGB", size, NIGHT)
    img = ImageChops.add(img, glow(size, (w * 0.5, h * 0.45), w * 0.4, SLATE, 0.18))
    lines = Image.new("RGB", size, (0, 0, 0))
    d = ImageDraw.Draw(lines)
    for c in range(cols + 1):
        d.line([(ox + c * cell, oy), (ox + c * cell, oy + rows * cell)], fill=(24, 30, 46), width=1)
    for r in range(rows + 1):
        d.line([(ox, oy + r * cell), (ox + cols * cell, oy + r * cell)], fill=(24, 30, 46), width=1)
    img = ImageChops.add(img, lines)
    center = lambda c, r: (ox + (c + 0.5) * cell, oy + (r + 0.5) * cell)
    tiles = Image.new("RGB", size, (0, 0, 0))
    t = ImageDraw.Draw(tiles)
    beams = Image.new("RGB", size, (0, 0, 0))
    b = ImageDraw.Draw(beams)
    used = set()

    def tile(c, r, fill=(30, 36, 52), edge=(70, 80, 108)):
        x, y = center(c, r)
        q = cell * 0.4
        t.rounded_rectangle([x - q, y - q, x + q, y + q], radius=cell * 0.14, fill=fill, outline=edge, width=2)
        used.add((c, r))

    for color in rnd.sample([ROSE, MOSS, SLATE, OCHRE, LAVENDER, SAGE], 3):
        c, r = rnd.randrange(1, cols - 1), rnd.randrange(rows)
        dc, dr = rnd.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        tile(c, r)
        pts = [center(c, r)]
        for _ in range(rnd.randint(2, 4)):
            steps = rnd.randint(2, 5)
            nc = min(max(c + dc * steps, 0), cols - 1)
            nr = min(max(r + dr * steps, 0), rows - 1)
            if (nc, nr) == (c, r):
                break
            c, r = nc, nr
            pts.append(center(c, r))
            tile(c, r)  # a mirror where the beam turns
            dc, dr = (dr, dc) if rnd.random() < 0.5 else (-dr, -dc)
        b.line(pts, fill=color, width=max(3, int(cell * 0.05)), joint="curve")
        x, y = pts[-1]
        q = cell * 0.22
        b.ellipse([x - q, y - q, x + q, y + q], outline=color, width=max(3, int(cell * 0.05)))
        b.ellipse([x - q * 0.45, y - q * 0.45, x + q * 0.45, y + q * 0.45], fill=color)
    for _ in range(rnd.randint(4, 8)):  # spare, unlit tiles
        c, r = rnd.randrange(cols), rnd.randrange(rows)
        if (c, r) not in used:
            tile(c, r, fill=(20, 24, 36), edge=(44, 52, 72))
    img = ImageChops.add(img, tiles)
    halo = beams.filter(ImageFilter.GaussianBlur(cell * 0.2)).point(lambda v: int(v * 0.9))
    img = ImageChops.add(img, halo)
    img = ImageChops.lighter(img, beams)
    return grain(img, 4)


def loop():
    """An 8-second, seamless, muted loop: a slow push in and back out over the board."""
    if not shutil.which("ffmpeg"):
        print("skipped loop.mp4 (no ffmpeg)")
        return
    frames = 240
    zoom = f"1.12-0.12*cos(2*PI*on/{frames})"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(OUT / "board.jpg"), "-vf",
         f"scale=2560:-2,zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
         f":d={frames}:s=1280x720:fps=30,format=yuv420p",
         "-frames:v", str(frames), "-an", "-c:v", "libx264", "-crf", "26", "-preset", "slow",
         "-movflags", "+faststart", str(OUT / "loop.mp4")],
        check=True,
    )
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "loop.mp4"), "-frames:v", "1",
                    "-q:v", "3", str(OUT / "loop-poster.jpg")], check=True)
    print("wrote loop.mp4, loop-poster.jpg")


if __name__ == "__main__":
    save(aurora(), "aurora.jpg")
    save(prism(), "prism.jpg")
    save(horizon(), "horizon.jpg")
    save(mist(), "mist.jpg")
    save(board(11), "board.jpg")
    for i, seed in enumerate((21, 35, 48, 52), 1):
        save(board(seed, (1280, 800), cols=10, rows=6), f"board-{i}.jpg")
    loop()
