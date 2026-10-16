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

# Run the test suite (builds first)
test: build
    uv run pytest -q

# Serve the reference site at http://localhost:8000 (mockups at /assets via the symlink)
serve port="8000":
    python3 -m http.server {{ port }} -d site

# Assemble the GitHub Pages site into _site/
site: build
    rm -rf _site
    mkdir -p _site
    cp -RL site/. _site/
    cp -R mockups _site/mockups
    touch _site/.nojekyll
