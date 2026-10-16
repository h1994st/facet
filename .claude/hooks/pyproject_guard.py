#!/usr/bin/env python3
"""Print a denial reason if a pending Edit/MultiEdit/Write changes guarded pyproject.toml data.

Reads the PreToolUse JSON on stdin, applies the edit to the current file in memory and compares
the parsed dependency data before and after. Prints nothing when the change is allowed.
"""

import json
import os
import sys
import tomllib
from pathlib import Path


def guarded(doc: dict) -> dict:
    project = doc.get("project", {})
    return {
        "dependencies": project.get("dependencies"),
        "optional-dependencies": project.get("optional-dependencies"),
        "requires-python": project.get("requires-python"),
        "dependency-groups": doc.get("dependency-groups"),
        "tool.uv.sources": doc.get("tool", {}).get("uv", {}).get("sources"),
    }


def main() -> None:
    data = json.load(sys.stdin)
    tool = data.get("tool_name")
    args = data.get("tool_input", {})
    path = Path(args.get("file_path", ""))
    if not path.is_absolute():
        path = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / path
    try:
        old = path.read_text() if path.exists() else ""
        before = guarded(tomllib.loads(old))
        if tool == "Write":
            new = args.get("content", "")
        else:
            edits = args.get("edits") or [args]
            new = old
            for e in edits:
                o, n = e.get("old_string", ""), e.get("new_string", "")
                if not o or o not in new:
                    print("edit cannot be applied to the current pyproject.toml; cannot verify it")
                    return
                new = new.replace(o, n) if e.get("replace_all") else new.replace(o, n, 1)
        after = guarded(tomllib.loads(new))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        print(f"cannot verify pyproject.toml change ({exc})")
        return
    if before != after:
        print(
            "pyproject.toml dependencies, groups, sources and requires-python change only via "
            "`uv add` / `uv remove` (use --dev for dev tools)."
        )


main()
