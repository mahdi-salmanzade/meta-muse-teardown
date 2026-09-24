#!/usr/bin/env bash
# Reproduce every evidence file in this repo from your own copy of Muse-3.0.dmg.
# Nothing here executes the app: the DMG is mounted read-only and only inspected.
#
#   ./scripts/reproduce.sh /path/to/Muse-3.0.dmg
set -euo pipefail

DMG="${1:?usage: $0 /path/to/Muse-3.0.dmg}"
WORK="$(mktemp -d)"
MNT="$WORK/mnt"
APP="$WORK/Muse.app"
C="$APP/Contents"

echo "[*] sha256 (expected 3818f35b89580d857f412977f6d8f5d409dbc3112da3e7119ea254d518010de4)"
shasum -a 256 "$DMG"

hdiutil attach -readonly -nobrowse -noautoopen -mountpoint "$MNT" "$DMG" >/dev/null
ditto "$MNT/Muse.app" "$APP"
hdiutil detach "$MNT" -quiet

echo; echo "[*] Signature"
codesign -dvvv "$APP" 2>&1 | grep -E "Identifier|Authority|TeamIdentifier|Timestamp"
spctl -a -vvv -t exec "$APP" 2>&1 | tail -2

echo; echo "[*] Entitlements"
codesign -d --entitlements - --xml "$APP" 2>/dev/null | plutil -p -

echo; echo "[*] Privacy usage strings (what macOS will ask you for)"
plutil -p "$C/Info.plist" | grep UsageDescription

strings -n 6 "$C/MacOS/Muse" > "$WORK/strings.txt"

echo; echo "[*] Local agent tools"
grep -oE "\b(imessage|email|notes|calendar|reminders|contacts|whatsapp|files|computer|screen|camera)\.[a-z_]+\b" "$WORK/strings.txt" | sort -u

echo; echo "[*] Background upload / sync machinery"
grep -E "SyncSource|Backfill|MediaSync|media_sync" "$WORK/strings.txt" | sort -u

echo; echo "[*] WhatsApp database access"
grep -E "ChatStorage|WhatsApp" "$WORK/strings.txt" | sort -u | head -20

echo; echo "[*] Remote VM endpoints"
grep -E "metaaivm|/hatch/" "$WORK/strings.txt" | sort -u

echo; echo "[*] Auto-sync consent copy (web UI)"
LC_ALL=C grep -aoE "function autoSyncCopy.{0,1800}" "$C/Resources/hatch/index.html" \
  | grep -oE "fbs\._\(\`[^\`]+\`" | sed 's/fbs._(`//;s/`$//'

echo; echo "[*] Bundled Chrome extension"
cat "$C/Resources/chrome/manifest.json"

echo; echo "[*] stealth.min.js header"
head -6 "$C/Resources/stealth.min.js"

echo; echo "[*] Extracted app left at: $APP"
