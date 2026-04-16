#!/usr/bin/env bash
# claude-bootstrap uninstaller
# Removes installed commands, scripts, bootstrap templates, and (optionally) swat-memory
# from ~/.claude/. Does NOT delete backups or the swat-memory DB.
#
# Usage:
#   ./uninstall.sh              # remove everything this repo installed
#   ./uninstall.sh --keep-memory

set -euo pipefail

REPO="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLAUDE_HOME="${HOME}/.claude"
KEEP_MEMORY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-memory) KEEP_MEMORY=true; shift ;;
    -h|--help)     sed -n '2,10p' "$0"; exit 0 ;;
    *)             echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

log()  { printf '→ %s\n' "$*"; }
warn() { printf '! %s\n' "$*" >&2; }
ok()   { printf '✓ %s\n' "$*"; }

remove_if_ours() {
  local repo_file="$1" installed="$2"
  if [[ ! -e "$installed" && ! -L "$installed" ]]; then return; fi
  # Only remove if it's a symlink pointing to our repo or a copy of our file
  if [[ -L "$installed" ]]; then
    local target
    target=$(readlink "$installed")
    if [[ "$target" == "$repo_file" ]]; then rm -f "$installed"; log "removed symlink $installed"; fi
  elif cmp -s "$repo_file" "$installed" 2>/dev/null; then
    rm -f "$installed"; log "removed $installed"
  else
    warn "kept $installed (modified locally)"
  fi
}

for f in "${REPO}/commands/"*.md; do
  remove_if_ours "$f" "${CLAUDE_HOME}/commands/$(basename "$f")"
done
for f in "${REPO}/scripts/"*.sh; do
  remove_if_ours "$f" "${CLAUDE_HOME}/scripts/$(basename "$f")"
done
for f in "${REPO}/bootstrap/"*.md; do
  remove_if_ours "$f" "${CLAUDE_HOME}/bootstrap/$(basename "$f")"
done

if [[ "$KEEP_MEMORY" == false && -d "${REPO}/tools/swat-memory" ]]; then
  log "uninstalling swat-memory"
  "${REPO}/tools/swat-memory/scripts/uninstall.sh" || warn "swat-memory uninstaller failed"

  SETTINGS="${CLAUDE_HOME}/settings.json"
  if [[ -f "$SETTINGS" ]]; then
    cp "$SETTINGS" "$SETTINGS.bak-uninstall-$(date +%Y%m%d-%H%M%S)"
    SETTINGS_FILE="$SETTINGS" python3 <<'PYEOF'
import json, os
from pathlib import Path
p = Path(os.environ["SETTINGS_FILE"])
data = json.loads(p.read_text())
data.get("mcpServers", {}).pop("swat-memory", None)
for event in ("SessionStart", "Stop"):
    entries = data.get("hooks", {}).get(event, [])
    entries[:] = [e for e in entries if not any(
        "swat-memory" in h.get("command", "") for h in e.get("hooks", [])
    )]
    if not entries and event in data.get("hooks", {}):
        data["hooks"].pop(event, None)
p.write_text(json.dumps(data, indent=2) + "\n")
print(f"✓ cleaned settings.json ({p})")
PYEOF
  fi
  warn "swat-memory DB preserved at ~/.claude/swat-memory/memory.db — delete manually for a clean slate"
else
  log "keeping swat-memory (--keep-memory or not installed)"
fi

ok "done"
