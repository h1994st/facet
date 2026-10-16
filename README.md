# facet

A shared design language for a family of websites: design tokens, components and brand assets in
plain CSS and small vanilla JS, so every site can use them without a build step and the sites read
as one family. The name: each site is one facet of the same identity, cut from the same glass.

## Principles

- Minimalist and modern, with glass and reflection as signature elements.
- Dark-first, with a full light theme.
- Each site keeps its own accent color on top of the shared system.
- English and Chinese from the start.
- Every animation has a still version for visitors who turn motion off.

## Design choices

- **Type:** Source Serif 4 and Noto Serif SC for headings, Geist for text and UI, Geist Mono for
  code. Chinese body text uses the system's built-in fonts; LXGW WenKai (霞鹜文楷) is available as
  an opt-in. All fonts are self-hosted alongside the sites, so they load wherever the sites do,
  including mainland China (`just fonts` rebuilds them from the pinned official releases).
- **Color:** low saturation throughout, on cool (slightly blue) neutral grays. Accents share one
  lightness and chroma in OKLCH, so every site's buttons and links have the same contrast.
- **Glass:** solid surfaces at rest, with frosted glass only on things that float (nav, sheets).
  Cards pick up a liquid-glass light that follows the pointer only on hover.
- **Shape:** continuous-curvature (squircle) corners everywhere: rounded containers, pill-shaped
  controls and round icons.

### Accents

Each site picks one accent; everything else is shared. An accent marks a family of related sites
(dev tools, games, writing), so sites in one family may share it; names, icons and the mascots tell
them apart.

| Accent   | OKLCH (dark / light)                 |
| -------- | ------------------------------------ |
| Rose     | 0.76 0.06 15 / 0.52 0.07 15          |
| Clay     | 0.76 0.06 55 / 0.52 0.07 55          |
| Ochre    | 0.76 0.06 85 / 0.52 0.07 85          |
| Moss     | 0.76 0.06 130 / 0.52 0.07 130        |
| Sage     | 0.76 0.06 165 / 0.52 0.07 165        |
| Teal     | 0.76 0.06 205 / 0.52 0.07 205        |
| Slate    | 0.76 0.06 255 / 0.52 0.07 255        |
| Lavender | 0.76 0.06 295 / 0.52 0.07 295        |
| Graphite | `#d5dbe3` / `#374151` (near-neutral) |

When the hues run out, add near-neutral accents: the same lightness (so the same contrast) at chroma
0.02 (0.025 on light), at least 70° apart.

| Near-neutral | OKLCH (dark / light)           |
| ------------ | ------------------------------ |
| Stone        | 0.76 0.02 70 / 0.52 0.025 70   |
| Lichen       | 0.76 0.02 150 / 0.52 0.025 150 |
| Steel        | 0.76 0.02 250 / 0.52 0.025 250 |
| Heather      | 0.76 0.02 320 / 0.52 0.025 320 |

## Mascots

Duna Feline (嘟娜·菲琳, gray tabby), Dudu (嘟嘟, solid gray) and Nangnang (囔囔, brown tabby). Duna
is the fictional owner of every sample in the mockups. Their drawing is copied from the my-resume
template's site.

## Use it

Reference site (tokens, color, type, components, layouts, the cast): https://shengtuo.me/facet/

Link `facet.css` first and `cast/cast-layered.css` after it (only needed for the mascots). From a
CDN, pinning a tag:

<!-- x-release-please-start-version -->

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/h1994st/facet@v0.1.0/dist/facet.css" />
<link
  rel="stylesheet"
  href="https://cdn.jsdelivr.net/gh/h1994st/facet@v0.1.0/dist/cast/cast-layered.css"
/>
<script
  type="module"
  src="https://cdn.jsdelivr.net/gh/h1994st/facet@v0.1.0/dist/js/facet.js"
></script>
```

<!-- x-release-please-end -->

Or as a git submodule, serving `vendor/facet/dist/` with your site (better for mainland China, where
jsDelivr is unreliable):

<!-- x-release-please-start-version -->

```sh
git submodule add https://github.com/h1994st/facet vendor/facet
git -C vendor/facet checkout v0.1.0
```

<!-- x-release-please-end -->

A minimal page:

```html
<html lang="en" data-accent="moss">
  <head>
    <link rel="stylesheet" href="/vendor/facet/dist/facet.css" />
    <script type="module" src="/vendor/facet/dist/js/facet.js"></script>
  </head>
  <body>
    <nav class="f-nav">…</nav>
    <main class="f-page f-prose">…</main>
  </body>
</html>
```

- `data-accent` picks the accent (see the tables above); `data-theme` is `dark` (default), `light`
  or `auto`. The theme toggle remembers its choice in `localStorage["facet-theme"]`.
- A plain `.f-nav` sits in the page flow. Add `.f-nav--fixed` to float it over the page; while one
  is present, `--f-nav-clear` reserves room for it at the top of the layouts (override it if your
  nav is taller).
- Everything is in `@layer facet.*`, so your own unlayered CSS wins without `!important`.
- Set `lang="zh-Hans"` on any element for Chinese typography.

## Layout

- `src/`: the source CSS, JS, cast and font slices. `dist/` is generated from it by `just build` and
  committed; never edit `dist/` by hand.
- `site/`: the reference site (`just serve`, or `just site` for the GitHub Pages bundle).
- `tests/`: browser tests (`just test`).
- `fonts/`: the font build (`just fonts`).
- `pyproject.toml`: the uv project for the Python tooling (fonts, images, tests).
- `mockups/`: design explorations (type, color, shape, glass, layout, the cats), viewable with
  `just serve` at http://localhost:8000/mockups/.
- `mockups/assets/craft.py`: draws the demo images and video loop the mockups use
  (`uv run mockups/assets/craft.py`; the loop needs ffmpeg).

## License

MIT. Fonts keep their own licenses (SIL OFL).
