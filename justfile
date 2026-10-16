set shell := ["bash", "-euo", "pipefail", "-c"]

# Files Prettier owns; dot-directories must be listed explicitly
prettier_globs := '"**/*.{css,js,mjs,html,md,json,yml,yaml}" ".claude/**/*.json"'

# List recipes
default:
    @just --list

# Install tooling
deps:
    brew bundle

# Format everything, or only the given files
fmt *files:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "{{ files }}" ]]; then
        py=(); other=()
        for f in {{ files }}; do [[ $f == *.py ]] && py+=("$f") || other+=("$f"); done
        if (( ${#py[@]} )); then
            uv run ruff format "${py[@]}"
            uv run ruff check --fix "${py[@]}"
        fi
        if (( ${#other[@]} )); then
            prettier --write --ignore-unknown "${other[@]}"
        fi
    else
        prettier --write {{ prettier_globs }}
        uv run ruff format .
        uv run ruff check --fix .
        just --fmt --unstable
    fi

# Check formatting and lint without changing files
check:
    prettier --check {{ prettier_globs }}
    uv run ruff format --check .
    uv run ruff check .
    just --fmt --check --unstable

# Build dist/ from src/
build:
    uv run scripts/build.py

# Rebuild the self-hosted fonts (downloads pinned releases)
fonts:
    uv run fonts/build.py

# Refetch the pinned social icons into src/icons/ (network; see icons/sources.toml)
icons:
    uv run icons/fetch.py

# Run the test suite (builds first)
test: build
    uv run pytest -q

# Serve the Pages layout (what `just site` assembles) at http://localhost:8000, live from site/
serve port="8000": build
    rm -rf _serve
    mkdir _serve
    for f in site/*; do [[ $f == site/tests ]] || ln -s "../$f" _serve/; done
    ln -s ../mockups _serve/mockups
    python3 -m http.server {{ port }} -d _serve

# Assemble the GitHub Pages site into _site/ (the test fixtures in site/tests stay out)
site: build
    rm -rf _site
    mkdir -p _site
    cp -RL site/. _site/
    rm -rf _site/tests
    cp -R mockups _site/mockups
    uv run scripts/site_meta.py _site
    touch _site/.nojekyll

# Redraw the reference site's share card and icon (site/card.png, site/favicon.svg)
card:
    uv run scripts/card.py
