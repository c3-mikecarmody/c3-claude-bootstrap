#!/usr/bin/env python3
"""SessionStart hook: derive a seed query from CWD + nearest CLAUDE.md,
run memory.recall, print a context block on stdout for Claude Code to inject."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add the package to sys.path so this script works without install.
_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

from swat_memory import db, recall  # noqa: E402


def _find_claude_md_h1(cwd: Path) -> str | None:
    for d in [cwd, *cwd.parents]:
        f = d / "CLAUDE.md"
        if f.exists():
            for line in f.read_text().splitlines():
                line = line.strip()
                if line.startswith("# "):
                    return line[2:].strip()
                if line:
                    # Fallback: first non-empty non-header line
                    return line[:120]
            return None
    return None


def _seed_query() -> str:
    cwd = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    base = cwd.name
    h1 = _find_claude_md_h1(cwd) or ""
    return f"{base} {h1}".strip()


def main() -> int:
    if os.environ.get("SWAT_MEMORY_SKIP_HOOK"):
        return 0
    query = _seed_query()
    if not query:
        return 0
    try:
        with db.session() as conn:
            hits = recall.recall(conn, query=query, k=5)
    except Exception as e:  # noqa: BLE001
        print(f"<!-- swat-memory session_start: {e} -->", file=sys.stderr)
        return 0

    if not hits:
        return 0

    lines = [f"<swat-memory seed={query!r}>"]
    for h in hits:
        if h["kind"] == "fact":
            lines.append(f"- [fact/{h['type']}] **{h['subject']}** — {h['content'][:200].strip()}")
        else:
            lines.append(f"- [episode imp={h['importance']:.1f}] {h['summary'][:200].strip()}")
    lines.append("</swat-memory>")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
