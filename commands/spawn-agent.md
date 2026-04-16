---
description: Open a new macOS Terminal window running an interactive Claude agent with a starter prompt, so Mike can take over after kickoff.
---

Spawn an independent, **headed** Claude Code session in a fresh Terminal window. Use this when Mike asks you to kick off parallel work he wants to steer interactively — not for fire-and-forget tasks (use the Agent tool for those).

## When to use

- Mike says "spin up an agent to…", "kick off a window for…", "open a terminal and have claude…"
- The work is long-running or needs hands-on direction after kickoff
- Mike wants to watch/intervene rather than wait for a background result

## How to call

Run the helper script — do **not** try to write osascript inline:

```bash
~/.claude/scripts/spawn-agent.sh <workdir> <prompt-or-@file> [--system <text-or-@file>]
```

- `<workdir>` — absolute or `~`-path to where the agent should start. Must exist.
- `<prompt>` — inline string, OR `@/path/to/file.md` to load from a file. Prefer `@file` for anything longer than a sentence (write the prompt to a tempfile first with Write, then pass `@<path>`). Avoids shell-quoting headaches.
- `--system <text-or-@file>` — optional. Appends to the system prompt via `claude --append-system-prompt`. Use for persona/role ("You are a 10th-century scop…"). The Claude Code harness identity cannot be replaced, only appended to. Same `@file` convention works.

### Env overrides

- `SPAWN_AGENT_TERMINAL=iterm` — use iTerm2 instead of Terminal.app
- `SPAWN_AGENT_CLAUDE=/path/to/claude` — override the `claude` binary

## Prompt authoring tips

The spawned agent inherits Mike's global `~/.claude/CLAUDE.md` and the target repo's `CLAUDE.md`, so don't restate preferences. **Do** include:

- Goal in one line
- Concrete first step
- Any context it can't derive from files (ticket links, decisions made in *this* session)
- A pointer to hand off back to Mike when stuck, not to ask you

## Arguments

`$ARGUMENTS` is free-form — typically "in `<dir>`, have an agent do `<task>`". Parse the dir and task, write the prompt to a tempfile, then invoke the script.

$ARGUMENTS
