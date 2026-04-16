#!/bin/bash
# spawn-agent.sh — open a new macOS Terminal window running an interactive `claude` session.
#
# Usage:
#   spawn-agent.sh <workdir> <prompt-or-@file> [--system <text-or-@file>]
#
# Examples:
#   spawn-agent.sh ~/Documents/foo "Refactor bar.js to use async/await"
#   spawn-agent.sh ~/Documents/foo @/tmp/my-prompt.md
#   spawn-agent.sh ~/Documents/foo @/tmp/prompt.md --system "You are a 10th-century scop..."
#   spawn-agent.sh ~/Documents/foo "compose verse" --system @/tmp/scop-system.md
#
# Env:
#   SPAWN_AGENT_TERMINAL=iterm   # use iTerm2 instead of Terminal.app (default: terminal)
#   SPAWN_AGENT_CLAUDE=claude    # override claude binary (default: claude on PATH)
#
# Notes:
#   --system uses claude's --append-system-prompt under the hood. The harness
#   identity cannot be replaced, only appended to.

set -euo pipefail

WORKDIR=""
PROMPT_ARG=""
SYSTEM_ARG=""

# Positional: workdir, prompt. Optional: --system <val>.
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --system)
      SYSTEM_ARG="${2:?--system requires a value}"
      shift 2
      ;;
    --system=*)
      SYSTEM_ARG="${1#--system=}"
      shift
      ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [[ ${#POSITIONAL[@]} -lt 2 ]]; then
  echo "Usage: $0 <workdir> <prompt-or-@file> [--system <text-or-@file>]" >&2
  exit 1
fi

WORKDIR="${POSITIONAL[0]}"
PROMPT_ARG="${POSITIONAL[1]}"

if [[ ! -d "$WORKDIR" ]]; then
  echo "Error: workdir not found: $WORKDIR" >&2
  exit 1
fi
WORKDIR="$(cd "$WORKDIR" && pwd)"

# Resolve a "text or @file" arg to a file on disk the launcher will read at exec time.
# Sets <out-file-var> and <out-cleanup-var> (true/false).
resolve_to_file() {
  local arg="$1" file_var="$2" cleanup_var="$3" label="$4"
  local file cleanup
  if [[ "$arg" == @* ]]; then
    file="${arg:1}"
    if [[ ! -f "$file" ]]; then
      echo "Error: $label file not found: $file" >&2
      exit 1
    fi
    cleanup=false
  else
    file="$(mktemp "/tmp/spawn-agent-${label}-XXXXXX")"
    printf '%s' "$arg" > "$file"
    cleanup=true
  fi
  printf -v "$file_var" '%s' "$file"
  printf -v "$cleanup_var" '%s' "$cleanup"
}

resolve_to_file "$PROMPT_ARG" PROMPT_FILE CLEANUP_PROMPT "prompt"

SYSTEM_FILE=""
CLEANUP_SYSTEM=false
if [[ -n "$SYSTEM_ARG" ]]; then
  resolve_to_file "$SYSTEM_ARG" SYSTEM_FILE CLEANUP_SYSTEM "system"
fi

CLAUDE_BIN="${SPAWN_AGENT_CLAUDE:-claude}"

# Build a launcher script Terminal will exec. This avoids AppleScript quoting hell.
LAUNCHER="$(mktemp /tmp/spawn-agent-launcher-XXXXXX)"
{
  echo '#!/bin/bash'
  echo "cd \"$WORKDIR\""
  echo 'echo "── spawned agent ──"'
  echo "echo \"workdir: $WORKDIR\""
  echo "echo \"prompt:  $PROMPT_FILE\""
  if [[ -n "$SYSTEM_FILE" ]]; then
    echo "echo \"system:  $SYSTEM_FILE\""
  fi
  echo 'echo "───────────────────"'
  if [[ -n "$SYSTEM_FILE" ]]; then
    echo "\"$CLAUDE_BIN\" --append-system-prompt \"\$(cat '$SYSTEM_FILE')\" \"\$(cat '$PROMPT_FILE')\""
  else
    echo "\"$CLAUDE_BIN\" \"\$(cat '$PROMPT_FILE')\""
  fi
  echo 'EXIT=$?'
  [[ "$CLEANUP_PROMPT" == true ]] && echo "rm -f '$PROMPT_FILE'"
  [[ "$CLEANUP_SYSTEM" == true ]] && echo "rm -f '$SYSTEM_FILE'"
  echo "rm -f '$LAUNCHER'"
  echo 'exit $EXIT'
} > "$LAUNCHER"
chmod +x "$LAUNCHER"

TERMINAL="${SPAWN_AGENT_TERMINAL:-terminal}"
case "$TERMINAL" in
  iterm|iterm2)
    osascript <<EOF
tell application "iTerm"
  activate
  create window with default profile command "$LAUNCHER"
end tell
EOF
    ;;
  *)
    osascript <<EOF
tell application "Terminal"
  activate
  do script "$LAUNCHER"
end tell
EOF
    ;;
esac

echo "Spawned agent → $WORKDIR (launcher: $LAUNCHER)"
