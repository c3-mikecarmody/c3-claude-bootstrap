#!/usr/bin/env bash
# Uninstall swat-memory. Leaves the DB file in place for backup; remove manually if desired.
set -euo pipefail

PLIST="${HOME}/Library/LaunchAgents/com.c3.swat-memory.maintenance.plist"
if [[ -f "${PLIST}" ]]; then
  launchctl unload "${PLIST}" || true
  rm "${PLIST}"
  echo "✓ launchd plist removed"
fi

echo "→ remove the mcpServers and hooks blocks for 'swat-memory' from ~/.claude/settings.json manually."
echo "→ DB preserved at ~/.claude/swat-memory/memory.db (delete if you want a clean slate)."
