#!/usr/bin/env bash
# claude-bootstrap installer
# Copies commands, scripts, and bootstrap templates into ~/.claude/, and
# optionally installs the swat-memory MCP server + hooks.
#
# Usage:
#   ./install.sh                # copy files, install swat-memory (default)
#   ./install.sh --no-memory    # skip swat-memory
#   ./install.sh --link         # symlink commands/scripts/bootstrap instead of copy
#   ./install.sh --force        # overwrite existing files (always backs up)
#   ./install.sh -h | --help

set -euo pipefail

REPO="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLAUDE_HOME="${HOME}/.claude"
BACKUP_DIR="${CLAUDE_HOME}/.bootstrap-backup-$(date +%Y%m%d-%H%M%S)"

INSTALL_MEMORY=true
MODE="copy"          # copy | link
FORCE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-memory)   INSTALL_MEMORY=false; shift ;;
    --with-memory) INSTALL_MEMORY=true;  shift ;;
    --link)        MODE="link";          shift ;;
    --force)       FORCE=true;           shift ;;
    -h|--help)     sed -n '2,13p' "$0"; exit 0 ;;
    *)             echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

log() { printf '→ %s\n' "$*"; }
warn() { printf '! %s\n' "$*" >&2; }
ok()  { printf '✓ %s\n' "$*"; }

mkdir -p "${CLAUDE_HOME}/commands" "${CLAUDE_HOME}/scripts" "${CLAUDE_HOME}/bootstrap"

# Place a file: back up any existing target, then copy or symlink.
place() {
  local src="$1" dst="$2"
  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ "$FORCE" == false ]] && ! cmp -s "$src" "$dst" 2>/dev/null; then
      mkdir -p "$BACKUP_DIR/$(dirname "${dst#${CLAUDE_HOME}/}")"
      cp "$dst" "$BACKUP_DIR/${dst#${CLAUDE_HOME}/}"
      warn "backed up $dst → $BACKUP_DIR/${dst#${CLAUDE_HOME}/}"
    fi
    rm -f "$dst"
  fi
  if [[ "$MODE" == "link" ]]; then
    ln -s "$src" "$dst"
  else
    cp "$src" "$dst"
  fi
}

log "installing commands → ${CLAUDE_HOME}/commands/"
for f in "${REPO}/commands/"*.md; do
  place "$f" "${CLAUDE_HOME}/commands/$(basename "$f")"
done

log "installing scripts → ${CLAUDE_HOME}/scripts/"
for f in "${REPO}/scripts/"*.sh; do
  place "$f" "${CLAUDE_HOME}/scripts/$(basename "$f")"
  chmod +x "${CLAUDE_HOME}/scripts/$(basename "$f")"
done

log "installing bootstrap templates → ${CLAUDE_HOME}/bootstrap/"
for f in "${REPO}/bootstrap/"*.md; do
  place "$f" "${CLAUDE_HOME}/bootstrap/$(basename "$f")"
done

# Seed ~/.claude/CLAUDE.md from the global template IF none exists.
# This ensures the first Claude Code session sees the [BOOT:] placeholders and
# prompts the user to run /first-boot --global. Never overwrites an existing file.
GLOBAL_CLAUDE="${CLAUDE_HOME}/CLAUDE.md"
SEEDED_CLAUDE=false
if [[ ! -e "$GLOBAL_CLAUDE" ]]; then
  log "seeding ${GLOBAL_CLAUDE} from global template (so first session prompts for onboarding)"
  cp "${REPO}/bootstrap/CLAUDE.global.template.md" "$GLOBAL_CLAUDE"
  SEEDED_CLAUDE=true
else
  log "${GLOBAL_CLAUDE} already exists — leaving it alone"
fi

ok "base install complete"

if [[ -d "$BACKUP_DIR" ]]; then
  warn "collisions backed up to: $BACKUP_DIR"
fi

# ─── swat-memory ───────────────────────────────────────────────────────────
if [[ "$INSTALL_MEMORY" == true ]]; then
  SWAT_MEMORY_ROOT="${REPO}/tools/swat-memory"
  if [[ ! -d "$SWAT_MEMORY_ROOT" ]]; then
    warn "tools/swat-memory not present — skipping memory install"
  else
    log "installing swat-memory from ${SWAT_MEMORY_ROOT}"
    "${SWAT_MEMORY_ROOT}/scripts/install.sh"

    SETTINGS="${CLAUDE_HOME}/settings.json"
    if [[ -f "$SETTINGS" ]]; then
      cp "$SETTINGS" "$SETTINGS.bak-$(date +%Y%m%d-%H%M%S)"
      log "backed up settings.json"
    else
      echo '{}' > "$SETTINGS"
    fi

    log "merging swat-memory config into settings.json"
    PY="${SWAT_MEMORY_ROOT}/.venv/bin/python"
    SM_ROOT="$SWAT_MEMORY_ROOT" SM_PY="$PY" SETTINGS_FILE="$SETTINGS" python3 <<'PYEOF'
import json, os, sys
from pathlib import Path

settings_path = Path(os.environ["SETTINGS_FILE"])
root = os.environ["SM_ROOT"]
py = os.environ["SM_PY"]

try:
    data = json.loads(settings_path.read_text()) if settings_path.stat().st_size else {}
except json.JSONDecodeError as e:
    print(f"✗ settings.json is not valid JSON ({e}); aborting merge", file=sys.stderr)
    sys.exit(1)

mcp = data.setdefault("mcpServers", {})
mcp["swat-memory"] = {"command": py, "args": ["-m", "swat_memory"]}

hooks = data.setdefault("hooks", {})
for event, script in (("SessionStart", "session_start.py"), ("Stop", "stop_summarize.py")):
    entries = hooks.setdefault(event, [])
    cmd = f"{root}/hooks/{script}"
    # Remove any prior swat-memory entry so we don't accumulate duplicates
    entries[:] = [e for e in entries if not any(
        h.get("command", "").endswith(script) for h in e.get("hooks", [])
    )]
    entries.append({"matcher": "*", "hooks": [{"type": "command", "command": cmd}]})

settings_path.write_text(json.dumps(data, indent=2) + "\n")
print(f"✓ settings.json updated ({settings_path})")
PYEOF

    ok "swat-memory installed and registered"
  fi
else
  log "skipping swat-memory (--no-memory)"
fi

ok "install complete"

# ─── Next steps banner ─────────────────────────────────────────────────────
cat <<BANNER

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Next steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Restart Claude Code (or start a new session) so it picks up the new
     commands, templates, hooks, and MCP server.

BANNER

if [[ "$SEEDED_CLAUDE" == true ]]; then
  cat <<BANNER
  2. On your first session, Claude will notice the placeholders in
     ~/.claude/CLAUDE.md and offer to run /first-boot --global. Say yes —
     it's a ~5-minute conversational interview that populates your identity,
     communication preferences, and environment.

     You can also run it manually any time:
         /first-boot --global      # interview for ~/.claude/CLAUDE.md
         /first-boot               # run in a project dir to scaffold ./CLAUDE.md

BANNER
else
  cat <<BANNER
  2. Your existing ~/.claude/CLAUDE.md was preserved. To refresh it with the
     new onboarding flow, run:
         /first-boot --global      # augment interactively

     For per-project onboarding, cd into a project and run:
         /first-boot               # scaffolds ./CLAUDE.md

BANNER
fi

if [[ "$INSTALL_MEMORY" == true ]]; then
  cat <<BANNER
  3. (Optional) Migrate any existing markdown auto-memory from a project
     you've been using:
         cd /path/to/your/project
         source "${SWAT_MEMORY_ROOT}/.venv/bin/activate"
         python -m swat_memory.migrate_markdown --dry-run   # preview
         python -m swat_memory.migrate_markdown             # real run

BANNER
fi

cat <<BANNER
  Custom commands now available:
    /plan  /review  /catchup  /document  /debug  /commit
    /spawn-agent  — open a new Terminal running a directed Claude agent
    /first-boot   — onboarding interview (global or per-project)

  See: README.md and TOOLING.md in this repo for design notes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BANNER
