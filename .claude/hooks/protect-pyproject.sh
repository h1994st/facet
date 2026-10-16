#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) hook: pyproject.toml dependencies change only through
# `uv add` / `uv remove` (see CLAUDE.md). Other sections may be edited directly.
# The edit is applied in memory and the parsed dependency data compared (pyproject_guard.py).
set -euo pipefail

input=$(cat)
file=$(jq -r '.tool_input.file_path // empty' <<<"$input")
[[ $(basename "$file") == pyproject.toml ]] || exit 0

reason=$(python3 -I "$(dirname "$0")/pyproject_guard.py" <<<"$input")
[[ -n $reason ]] || exit 0

jq -n --arg reason "$reason" '{hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $reason
}}'
