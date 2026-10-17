# CLAUDE.md

Guidance for Claude Code in this repository. What facet is and who uses it: `README.md`.

## Commands

```bash
brew bundle        # install tooling (just, prettier); `just deps` does the same
uv sync            # install the Python environment from uv.lock
just               # list recipes
just fmt [files]   # format everything, or only the given files
just check         # check formatting without changing files
just build         # generate dist/ from src/
just test          # build, then run the browser tests (pytest + Playwright)
just fonts         # rebuild the self-hosted fonts (network; cached in fonts/.cache/)
just icons         # refetch the pinned social icons into src/icons/ (network)
just serve         # build, then serve site/ + mockups/ live at http://localhost:8000
just site          # assemble the GitHub Pages site into _site/ (what CI deploys; no site/tests)
just card          # redraw the share card and icon (site/card.png, site/favicon.svg)
just banner        # redraw the README banners (.github/readme/banner-*.png)
just shots         # retake the README screenshots (.github/readme/*.webp)
```

## Repository layout

- `src/`: the source (`css/` numbered files concatenate into `dist/facet.css`; `js/`, `cast/`,
  `fonts/`). `src/icons/` is written by `just icons` from `icons/sources.toml`; never hand-edit it.
- `dist/`: generated and committed (consumers load it from jsDelivr or a submodule); never edit it.
- `site/`: the reference site and the docs. `site.js` (a classic `<head>` script) applies theme,
  language and accent before paint and renders the toolbar; `site.css` is only toolbar and swatch
  styles; `site/tests/` holds test fixtures. Every page has a `<title>` and a
  `<meta name="description">`, each with a `data-zh`. `scripts/site_meta.py` (`just site`) writes
  the `zh/` copies, canonical, `hreflang`, Open Graph and JSON-LD tags and `sitemap.xml`: never
  hand-write those.
- `scripts/card.py`, `banner.py` and `shots.py` draw `site/card.png`, `site/favicon.svg` and the
  README images in `.github/readme/`: edit the scripts, not the images.
- `tests/`: Playwright tests against `site/` (contrast helpers in `checks.py`). `mockups/`: design
  explorations, left as is.

Cascade layers, in order: `facet.reset`, `.tokens`, `.base`, `.prose`, `.cast`, `.components`,
`.layouts`, `.utilities`. Unlayered consumer CSS wins, except over the only two layered `!important`
rules (`[hidden]`, the reduced-motion block); keep it to those two.

## Engineering rules

- **No build step for consumers.** Plain CSS (custom properties, classes) and small, optional
  vanilla JS; no framework, no preprocessor output a consumer must compile.
- **Every token has a dark and a light value.** Dark is designed first; no `data-theme` follows the
  system. A themed token is one declaration in `10-tokens.css`,
  `var(--f-unless-light, <dark>) var(--f-unless-dark, <light>)`: never a per-theme block, never a
  token for one theme only.
- **Low saturation.** In OKLCH, accents at chroma 0.08 or below, neutrals 0.02 or below; no
  saturated hues anywhere, illustrations and semantic colors included.
- **Accents** vary by hue only: `oklch(0.76 0.06 H)` dark, `oklch(0.52 0.07 H)` light; never raise
  chroma or change lightness to stand out. A new one takes a free hue at least 30° from the others
  on `site/color.html` (record it there), guided by the project's imagery; a family of related sites
  may share one. When hues run out, add near-neutrals (chroma 0.02 dark, 0.025 light, 70° apart).
  Status colors reuse Moss, Ochre, Rose and Slate, so alerts always carry an icon and a label.
  Components read the accent from a custom property, never a site's color.
- **Bilingual.** Test every component in English and Chinese (`lang="zh-Hans"`); never assume Latin
  widths. Chinese gets its own line-height, `letter-spacing: 0` and breaks between any two
  characters; never `word-break: keep-all`.
- **Fonts.** Source Serif 4 (Noto Serif SC) for headings, Geist for text and UI, Geist Mono for
  code; Chinese body text uses system fonts. Self-host every font, never a third-party host (Google
  and jsDelivr fail in mainland China): built from official releases by a committed fontTools
  script, output committed. Latin ships as variable WOFF2 subset to Latin; Chinese (Noto Serif SC,
  the opt-in LXGW WenKai) as one weight in Google's frequency-based `unicode-range` slices. Every
  `@font-face` sets `font-display: swap`; every stack ends in system fonts.
- **Corner shapes.** `corner-shape` (`squircle`, `bevel`) is Chromium-only: every shape must read as
  a plain `border-radius` arc in Safari (including iOS) and Firefox; a cut corner that must survive
  needs `clip-path`. Squircle only on containers and tiles; pills and circles stay `round`.
- **Responsive.** Breakpoints 640px and 1024px; collapse only when content stops fitting
  (side-by-side holds to 721px). Check every page at 390, 860 and 1280px in both languages, with no
  horizontal scroll. Grid tracks use `minmax(0, 1fr)`, never `1fr`. On phones, at most the nav plus
  one sticky element, never covering content. Hover-only effects are decoration; interactive things
  need a touch path and look tappable. Track scroll on `scroll`, not an IntersectionObserver band.
- **Motion.** Every animation has a still fallback under `prefers-reduced-motion: reduce`.
- **The cats.** Copy them verbatim from the my-resume template's `site` branch (`site/cast.js`,
  `.cat[data-cat=…]` in `site/style.css`) into `src/cast/` and `mockups/cast/`, with the source
  commit in a header comment and out of Prettier; never redraw or recolor them, nor `!important`
  past their `facet.cast` layer. Cats are `aria-hidden`, never cover text, and get a faint white
  outline (`--cat-edge`) on dark.
- **No personal information.** Samples use Duna Feline's fictional world (example.com) and the art
  from `mockups/assets/craft.py`; never real names, domains, accounts, employers, local paths or
  personal stories.
- **American English** in code, comments, docs and UI text, except verbatim copies from other repos.

## Git

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/), body empty unless one
  or two short sentences on why are needed. No attribution lines.
- **Branches:** [Conventional Branch](https://conventional-branch.github.io/) off `main`
  (`feature/`, `bugfix/`, `hotfix/`, `release/<version>`, `chore/`), lowercase with hyphens.
- **Merging:** always squash merge into `main` (`git merge --squash`, one Conventional Commit); no
  merge commits. `.claude/hooks/protect-history.sh` denies any other `git merge`.
- **Releases:** release-please versions from the squashed titles (`feat:` minor, `fix:` patch,
  `feat!:` major). Never edit the version or changelog by hand.

## Tooling

- **Dependencies:** never edit `Brewfile` (`brew bundle add` / `remove`), `pyproject.toml` or
  `uv.lock` (`uv add` / `uv remove`, `--dev` for dev tools); hooks in `.claude/` enforce it.
- **Formatting:** Prettier owns CSS, JS, HTML, Markdown, JSON and YAML; Ruff owns Python;
  `just --fmt` the justfile. A hook runs `just fmt <file>` after each edit; run `just check` first.
- **CI** (`ci.yml`): `just check` (Prettier pinned to the Brewfile's version; bump both together),
  `just build` with `dist/` unchanged, and `just test`. `pages.yml` deploys `just site` from `main`.
