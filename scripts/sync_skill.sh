#!/usr/bin/env bash
# Re-vendor the official Futu skill pack into src/futu_opend_mcp/_skill/.
# Usage: ./scripts/sync_skill.sh
set -euo pipefail
DEST="src/futu_opend_mcp/_skill"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -sSL -o "$TMP/opend-skills.zip" "https://openapi.futunn.com/skills/opend-skills.zip"
unzip -q "$TMP/opend-skills.zip" -d "$TMP"
rm -rf "$DEST/futuapi"
mkdir -p "$DEST"
cp -R "$TMP/skills/futuapi" "$DEST/futuapi"
# LEGAL_*.md live at the skills/ root (outside futuapi/); copy them in for
# attribution alongside the vendored pack.
cp "$TMP"/skills/LEGAL_*.md "$DEST/futuapi/" 2>/dev/null || true
echo "Vendored futuapi skill pack to $DEST/futuapi"
echo "Review with: git diff --stat"
