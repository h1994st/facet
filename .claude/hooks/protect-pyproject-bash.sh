#!/usr/bin/env bash
# PreToolUse(Bash) hook: deny shell commands that would modify pyproject.toml or uv.lock.
# They change only through `uv add|remove|lock|sync` (see CLAUDE.md).
set -euo pipefail

cmd=$(jq -r '.tool_input.command // empty')

# Not about these files: allow.
grep -Eq 'pyproject\.toml|uv\.lock' <<<"$cmd" || exit 0

# A single `uv add|remove|lock|sync ...` command (no chaining or redirection): allow.
# Newlines and command substitution can smuggle a second command past the per-line regex.
if [[ $cmd != *$'\n'* && $cmd != *'$('* && $cmd != *'`'* ]] &&
    grep -Eq '^[[:space:]]*uv[[:space:]]+(add|remove|lock|sync)([[:space:]][^;&|<>]*)?$' <<<"$cmd"; then
    exit 0
fi

# Anything that looks like a write while they are mentioned: deny.
# Redirects to /dev/null or fd duplication (2>&1) are not writes.
stripped=$(sed -E 's/[0-9]*>{1,2}[[:space:]]*(\/dev\/null|&[0-9-])//g' <<<"$cmd")
write_re='>|\btee\b|\b(sed|perl|ruby)\b[^|;&]*[[:space:]]-[a-zA-Z]*i|\b(mv|cp|rm|ln|install|truncate|dd|touch|patch)\b|\b(python3?|node|awk|ed|ex|vi|vim|nvim)\b|\bgit[[:space:]]+(checkout|restore|apply|stash|reset)\b'
if grep -Eq "$write_re" <<<"$stripped"; then
    jq -n '{hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: "pyproject.toml and uv.lock must not be edited from the shell; use `uv add` / `uv remove` / `uv lock`."
    }}'
fi
exit 0
