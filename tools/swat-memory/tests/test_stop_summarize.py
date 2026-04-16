"""Unit tests for the Stop hook transcript parser — the most likely first-week failure."""
import json
import sys
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parents[1] / "hooks"
sys.path.insert(0, str(HOOK_DIR))

import stop_summarize as ss  # noqa: E402


def _write_jsonl(path: Path, events: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(e) for e in events))


def test_extracts_anthropic_block_content(tmp_path):
    p = tmp_path / "t.jsonl"
    _write_jsonl(p, [
        {"type": "user", "message": {"role": "user", "content": "hello world"}},
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "hi there"},
                    {"type": "tool_use", "name": "Read"},
                    {"type": "text", "text": "done"},
                ],
            },
        },
    ])
    out = ss._read_transcript(p)
    assert "USER: hello world" in out
    assert "ASSISTANT:" in out
    assert "hi there" in out
    assert "done" in out
    assert "[tool_use:Read]" in out


def test_skips_system_and_unknown_roles(tmp_path):
    p = tmp_path / "t.jsonl"
    _write_jsonl(p, [
        {"type": "system", "message": {"role": "system", "content": "ignore me"}},
        {"type": "user", "message": {"role": "user", "content": "keep me"}},
    ])
    out = ss._read_transcript(p)
    assert "ignore me" not in out
    assert "keep me" in out


def test_tolerates_malformed_lines(tmp_path):
    p = tmp_path / "t.jsonl"
    p.write_text('\n'.join([
        'not json at all',
        json.dumps({"type": "user", "message": {"role": "user", "content": "survived"}}),
        '',
    ]))
    assert "survived" in ss._read_transcript(p)


def test_missing_file_returns_empty(tmp_path):
    assert ss._read_transcript(tmp_path / "nope.jsonl") == ""


def test_tool_result_content(tmp_path):
    p = tmp_path / "t.jsonl"
    _write_jsonl(p, [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [{"type": "tool_result", "content": "output of the tool"}],
            },
        },
    ])
    out = ss._read_transcript(p)
    assert "[tool_result] output of the tool" in out
