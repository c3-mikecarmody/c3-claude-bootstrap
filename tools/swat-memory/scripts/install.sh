#!/usr/bin/env bash
# Install swat-memory: venv + deps + launchd plist. Idempotent.
set -euo pipefail

REPO="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
LAUNCHD_DIR="${HOME}/Library/LaunchAgents"
PLIST_NAME="com.c3.swat-memory.maintenance.plist"
TARGET_PLIST="${LAUNCHD_DIR}/${PLIST_NAME}"

echo "→ repo: ${REPO}"

PYTHON_BIN="${SWAT_MEMORY_PYTHON:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  for candidate in python3.13 python3.12 python3.11; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      PYTHON_BIN="$(command -v "${candidate}")"
      break
    fi
  done
fi
if [[ -z "${PYTHON_BIN}" ]]; then
  echo "✗ no python >= 3.11 found. Install via: brew install python@3.12" >&2
  exit 1
fi
echo "→ python: ${PYTHON_BIN} ($(${PYTHON_BIN} --version))"

if [[ ! -d "${REPO}/.venv" ]]; then
  echo "→ creating venv"
  "${PYTHON_BIN}" -m venv "${REPO}/.venv"
fi

# shellcheck source=/dev/null
source "${REPO}/.venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -e "${REPO}"

mkdir -p "${HOME}/.claude/swat-memory" "${LAUNCHD_DIR}"

echo "→ rendering plist → ${TARGET_PLIST}"
sed -e "s|__REPO__|${REPO}|g" -e "s|__HOME__|${HOME}|g" \
  "${REPO}/hooks/${PLIST_NAME}" > "${TARGET_PLIST}"

if launchctl list | grep -q com.c3.swat-memory.maintenance; then
  launchctl unload "${TARGET_PLIST}" || true
fi
launchctl load "${TARGET_PLIST}"

echo "✓ installed. next: add the mcpServers + hooks blocks from README.md to ~/.claude/settings.json,"
echo "  then run: python3 -m swat_memory.migrate_markdown"
