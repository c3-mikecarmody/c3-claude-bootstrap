#!/usr/bin/env python3
"""Stop hook: read transcript path from hook stdin JSON, summarize with `claude -p`,
persist an episode. Fails silently — hook must never block Claude Code's exit."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

from swat_memory import db, episodes  # noqa: E402

MAX_TRANSCRIPT_CHARS = 16000
SUMMARY_PROMPT = (
    "Summarize the following Claude Code session in 3-5 sentences for a persistent "
    "memory store. Focus on: what was worked on, decisions made, blockers, and "
    "anything worth recalling next session. Then on a new line output `TAGS:` "
    "followed by 3-6 comma-separated short tags (lowercase, kebab-case). "
    "Output only the summary and the TAGS line — no preamble."
)


def _extract_text(content) -> str:
    """Pull plain text out of Anthropic-style content: a string, or a list of
    {type, text}/{type:'tool_use'|'tool_result', ...} blocks."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
        elif btype == "tool_use":
            parts.append(f"[tool_use:{block.get('name', '?')}]")
        elif btype == "tool_result":
            inner = block.get("content")
            if isinstance(inner, str):
                parts.append(f"[tool_result] {inner[:400]}")
            elif isinstance(inner, list):
                parts.append(f"[tool_result] {_extract_text(inner)[:400]}")
    return "\n".join(p for p in parts if p)


def _read_transcript(path: Path) -> str:
    """Claude Code transcript is JSONL. Each line is typically
    {type: 'user'|'assistant', message: {role, content: str | [blocks]}, ...}.
    Some older lines may have flatter shapes; handle both defensively."""
    try:
        raw = path.read_text(errors="replace").splitlines()
    except FileNotFoundError:
        return ""
    turns = []
    for line in raw[-600:]:  # bound memory
        try:
            evt = json.loads(line)
        except ValueError:
            continue
        msg = evt.get("message")
        if isinstance(msg, dict):
            role = msg.get("role") or evt.get("type")
            text = _extract_text(msg.get("content"))
        else:
            # Fallback for flat shapes: {role, content} or {type, text}
            role = evt.get("role") or evt.get("type")
            text = _extract_text(evt.get("content")) or evt.get("text") or ""
        if role in ("user", "assistant") and text and text.strip():
            turns.append(f"{role.upper()}: {text.strip()}")
    joined = "\n".join(turns)
    return joined[-MAX_TRANSCRIPT_CHARS:]


def _summarize(transcript_text: str) -> tuple[str, list[str]]:
    prompt = f"{SUMMARY_PROMPT}\n\nSESSION:\n{transcript_text}"
    # Guard against recursion: the child `claude -p` inherits our settings.json,
    # so without this env flag it would fire stop_summarize.py again on exit.
    child_env = {**os.environ, "SWAT_MEMORY_SKIP_HOOK": "1"}
    try:
        out = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
            env=child_env,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(f"claude -p failed: {e}") from e

    tags: list[str] = []
    summary = out
    for line in out.splitlines():
        if line.strip().upper().startswith("TAGS:"):
            tag_blob = line.split(":", 1)[1]
            tags = [t.strip() for t in tag_blob.split(",") if t.strip()]
            summary = out.split(line, 1)[0].strip()
            break
    return summary, tags


def main() -> int:
    if os.environ.get("SWAT_MEMORY_SKIP_HOOK"):
        return 0
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    transcript_path = payload.get("transcript_path") or payload.get("transcript")
    if not transcript_path:
        return 0

    text = _read_transcript(Path(transcript_path))
    if len(text) < 200:  # nothing worth summarizing
        return 0

    try:
        summary, tags = _summarize(text)
    except RuntimeError as e:
        print(f"<!-- swat-memory stop_summarize: {e} -->", file=sys.stderr)
        return 0

    if not summary:
        return 0

    try:
        with db.session() as conn:
            conn.execute("BEGIN IMMEDIATE")
            episodes.save(conn, summary=summary, tags=tags)
            conn.execute("COMMIT")
    except Exception as e:  # noqa: BLE001
        print(f"<!-- swat-memory stop_summarize save: {e} -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
