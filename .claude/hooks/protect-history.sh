#!/usr/bin/env bash
# PreToolUse(Bash) hook: keep main's history linear. Branches go back to main as one squashed
# commit (`git merge --squash <branch>`, then `git commit`), so deny any other `git merge`.
set -euo pipefail

cmd=$(jq -r '.tool_input.command // empty')
grep -q 'git' <<<"$cmd" || exit 0

# Check each segment of a compound command separately.
while IFS= read -r seg; do
    grep -Eq '(^|[[:space:]])git([[:space:]]+-[Cc][[:space:]]+[^[:space:]]+)*[[:space:]]+merge([[:space:]]|$)' <<<"$seg" || continue
    # Aborting or continuing an in-progress merge is fine; so is a squash merge.
    grep -Eq '[[:space:]](--squash|--abort|--quit|--continue)([[:space:]]|$)' <<<"$seg" && continue
    jq -n '{hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: "Keep history linear: squash merge into main (`git merge --squash <branch>`, then commit), never a merge commit (see CLAUDE.md)."
    }}'
    exit 0
done < <(sed -E 's/(&&|\|\||;|\|)/\n/g' <<<"$cmd")
exit 0
