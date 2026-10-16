#!/usr/bin/env bash
# PostToolUse(Write|Edit|MultiEdit) hook: run `just fmt <file>` on files Prettier owns.
# Never blocks: formatting failures are left for `just check` to catch.
set -uo pipefail

file=$(jq -r '.tool_input.file_path // empty')

case "$file" in
    *.css | *.js | *.mjs | *.html | *.md | *.json | *.yml | *.yaml)
        cd "$CLAUDE_PROJECT_DIR" && just fmt "$file" >/dev/null 2>&1 ;;
esac
exit 0
