#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) hook: pyproject.toml dependencies change only through
# `uv add` / `uv remove` (see CLAUDE.md). Other sections may be edited directly.
# The edit is applied in memory and the parsed dependency data compared (pyproject_guard.py).
set -euo pipefail

input=$(cat)
# Fail closed: unreadable input or a crashing guard denies instead of letting the edit through.
file=$(jq -r '.tool_input.file_path // empty' <<<"$input") || file=pyproject.toml
[[ $(basename "$file") == pyproject.toml ]] || exit 0

reason=$(python3 -I "$(dirname "$0")/pyproject_guard.py" <<<"$input" 2>/dev/null) ||
    reason="pyproject guard failed; change dependencies with \`uv add\` / \`uv remove\`."
[[ -n $reason ]] || exit 0

jq -n --arg reason "$reason" '{hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $reason
}}'
