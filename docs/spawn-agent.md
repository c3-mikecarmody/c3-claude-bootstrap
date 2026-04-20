# `/spawn-agent` — headed agent in a new Terminal

Open an independent, interactive Claude Code session in a fresh macOS Terminal window, kicked off with a starter prompt. Used when you want to fan out parallel work you'll steer by hand after kickoff.

## When to use

- "Spin up an agent to refactor X while we talk about Y"
- Long-running or hands-on work that doesn't need to block the current session
- You want to watch and intervene, not wait for a background result

Not for fire-and-forget tasks — use the `Agent` subagent tool for those (it runs inside the current session without opening a window).

## Invocation

```bash
~/.claude/scripts/spawn-agent.sh <workdir> <prompt-or-@file> [--system <text-or-@file>]
```

Or from within Claude Code: `/spawn-agent <workdir> <prompt>`.

### Arguments

| Arg | Example | Notes |
|---|---|---|
| `<workdir>` | `~/projects/foo` | Absolute or `~`-path. Must exist. |
| `<prompt>` | `"Refactor bar.js to async/await"` | Inline string or `@/path/to/file.md`. |
| `--system` | `"You are a 10th-century scop..."` | Appends to system prompt via `--append-system-prompt`. Also accepts `@file`. |

### Env overrides

- `SPAWN_AGENT_TERMINAL=iterm` — use iTerm2 instead of Terminal.app
- `SPAWN_AGENT_CLAUDE=/path/to/claude` — override the `claude` binary

## Why `@file` for non-trivial prompts

Multi-line prompts going through shell + `osascript` + another shell layer turn into escaping hell. Instead:

```bash
# Write the prompt to a tempfile
cat > /tmp/my-prompt.md <<'EOF'
Multi-line prompt here.
With backticks: `like this`.
And "quotes" and 'quotes' without worry.
EOF

spawn-agent.sh ~/projects/foo @/tmp/my-prompt.md
```

The script reads the file via `cat` inside the new Terminal window, so content is never passed through AppleScript string literals.

## System prompt caveat

`--system` uses `claude --append-system-prompt` under the hood. The Claude Code harness identity ("You are Claude Code...") **cannot be replaced**, only appended to. For strong persona enforcement:

- Put persona rules in the `--system` string (stable across the session)
- Put the kickoff task in the positional `<prompt>` (the first user message)

If the persona needs to be very strict ("never break character"), also restate it in the prompt. The system prompt alone isn't always enough to override the harness's default behavior on follow-up turns.

## How it works under the hood

Three layers to sidestep macOS quoting:

1. **Launcher script** — `spawn-agent.sh` writes a fresh shell script to `/tmp/spawn-agent-launcher-XXXXXX` that contains:
   ```bash
   cd "<workdir>"
   claude "$(cat '<prompt-file>')"
   rm -f <launcher and tempfiles>
   ```
2. **osascript** — opens Terminal.app (or iTerm2) and runs `do script "<launcher-path>"`. No prompt content passes through AppleScript — just a path.
3. **Self-cleanup** — the launcher `rm`s itself and its tempfiles after `claude` exits.

### macOS `mktemp` gotcha

The script uses `mktemp /tmp/spawn-agent-launcher-XXXXXX` with no suffix. BSD `mktemp` on macOS doesn't substitute the `XXXXXX` if a suffix follows — `mktemp /tmp/foo-XXXXXX.sh` creates a file literally named `foo-XXXXXX.sh` and collides on the next call. We learned this the hard way. Don't add a suffix; `chmod +x` works fine without `.sh`.

See [../TOOLING.md](../TOOLING.md) for the full postmortem.

## iTerm2 support

Default is Terminal.app because it's always present on macOS. Set `SPAWN_AGENT_TERMINAL=iterm` (or `iterm2`) to use iTerm. Implementation uses `iTerm.create window with default profile command "<launcher>"`.

## Limitations

- **macOS only.** `osascript` and Terminal.app/iTerm.app are macOS-specific. No Linux or Windows equivalent wired up.
- **No return channel.** Spawned agent runs in its own window and process; results don't flow back to the parent session. If the parent agent needs to know what the child did, the child needs to write to a shared file/note.
- **One window per invocation.** No built-in multiplexing. Call the script multiple times for multiple windows.

For coordinated multi-agent orchestration (shared task list, inter-agent messaging, plan approval), Claude Code's Agent Teams runtime is the right tool — see `c3-e/c3toolsprompts` for `/team` integration. `/spawn-agent` is the lightweight "I just need a new window" option.

## Related

- [architecture.md](architecture.md) — where `spawn-agent.sh` lives and how the command is wired
