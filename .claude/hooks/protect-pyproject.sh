#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) hook: pyproject.toml dependencies change only through
# `uv add` / `uv remove` (see CLAUDE.md). Other sections may be edited directly.
set -euo pipefail

input=$(cat)
file=$(jq -r '.tool_input.file_path // empty' <<<"$input")
[[ $(basename "$file") == pyproject.toml ]] || exit 0

deny() {
    jq -n '{hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: "pyproject.toml dependencies change only via `uv add` / `uv remove` (use --dev for dev tools)."
    }}'
    exit 0
}

tool=$(jq -r '.tool_name // empty' <<<"$input")
[[ $tool == Write ]] && deny   # a whole-file rewrite can always touch dependencies

# Edit / MultiEdit: deny when an edited fragment mentions a dependency table or list.
fragments=$(jq -r '[.tool_input.old_string, .tool_input.new_string, (.tool_input.edits // [] | .[] | .old_string, .new_string)] | map(select(. != null)) | join("\n")' <<<"$input")
grep -Eq 'dependencies|dependency-groups|optional-dependencies|\[tool\.uv\.sources\]' <<<"$fragments" && deny
exit 0
