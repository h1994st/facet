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

# Assemble the GitHub Pages site into _site/
site:
    rm -rf _site
    mkdir -p _site
    cp -R mockups _site/mockups
    cp pages/index.html _site/index.html
    touch _site/.nojekyll

# Serve the repo to view mockups and demos
serve port="8000":
    python3 -m http.server {{ port }}
