#!/usr/bin/env bash
# Print the core macOS findings from your own copy of Muse-3.0.dmg.
# This is a console inspection, not a byte-for-byte rebuild of every evidence file.
# Nothing here executes the app: the DMG is mounted read-only and only inspected.
# Requires macOS command-line tools and Python 3.
#
#   ./scripts/reproduce.sh /path/to/Muse-3.0.dmg
set -euo pipefail
export LC_ALL=C

DMG="${1:?usage: $0 /path/to/Muse-3.0.dmg}"
WORK="$(mktemp -d)"
MNT="$WORK/mnt"
APP="$WORK/Muse.app"
C="$APP/Contents"
MOUNTED=0
cleanup() {
  if [[ "$MOUNTED" == 1 ]]; then
    if ! hdiutil detach "$MNT" -quiet; then
      echo "[!] Could not detach $MNT; leaving $WORK for manual cleanup." >&2
      return
    fi
  fi
  rm -rf "$WORK"
}
trap cleanup EXIT

echo "[*] sha256 (expected 3818f35b89580d857f412977f6d8f5d409dbc3112da3e7119ea254d518010de4)"
shasum -a 256 "$DMG"

hdiutil attach -readonly -nobrowse -noautoopen -mountpoint "$MNT" "$DMG" >/dev/null
MOUNTED=1
ditto "$MNT/Muse.app" "$APP"
hdiutil detach "$MNT" -quiet
MOUNTED=0

echo; echo "[*] Signature"
codesign -dvvv "$APP" 2>&1 | grep -E "Identifier|Authority|TeamIdentifier|Timestamp"
codesign --verify --deep --strict "$APP"
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
grep -E "ChatStorage|WhatsApp" "$WORK/strings.txt" | sort -u | sed -n '1,20p'

echo; echo "[*] Remote VM endpoints"
grep -E "metaaivm|/hatch/" "$WORK/strings.txt" | sort -u

echo; echo "[*] Auto-sync consent copy (web UI)"
python3 - "$C/Resources/hatch/index.html" <<'PY'
from pathlib import Path
import re
import sys
text = Path(sys.argv[1]).read_text()
start = text.index("function autoSyncCopy")
end = text.index("function ", start + len("function "))
copies = re.findall(r"fbs\._\(`([^`]+)`", text[start:end])
if not copies:
    raise SystemExit("No auto-sync copy found in this build")
print("\n".join(copies))
PY

echo; echo "[*] Bundled Chrome extension"
cat "$C/Resources/chrome/manifest.json"

echo; echo "[*] stealth.min.js header"
head -6 "$C/Resources/stealth.min.js"

echo; echo "[*] Inspection complete; temporary extraction removed on exit. Muse was not launched."
