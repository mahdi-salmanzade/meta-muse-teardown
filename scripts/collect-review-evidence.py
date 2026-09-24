#!/usr/bin/env python3
"""Collect bounded static evidence; never launch Muse or execute bundled scripts.

Run --help for inputs. Output directories are explicit, so verification can use
a temporary directory without overwriting the committed evidence.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import plistlib
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET


def run(*args):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode, result.stdout.decode(errors="replace"), result.stderr.decode(errors="replace")


def checked(*args):
    code, out, err = run(*args)
    if code:
        raise RuntimeError(f"{args[0]} failed ({code}): {err}")
    return out


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else hashlib.sha256(stream.read()).hexdigest()


def write(out, name, data):
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_text(data.rstrip() + "\n")


def excerpts(root, specifications):
    result = ["# Selected static excerpts; line numbers refer to the supplied extracted files.",
              "# JADX output may contain incorrect control flow; these are not runtime tests."]
    for relative, pattern in specifications:
        path = root / relative
        matches = [(i, line.strip()) for i, line in enumerate(path.read_text().splitlines(), 1)
                   if re.search(pattern, line)]
        if not matches:
            raise ValueError(f"No evidence matched {relative}: {pattern}")
        result.append(f"\n## {relative}")
        result.extend(f"{i}: {line[:900]}" for i, line in matches[:18])
    return "\n".join(result)


def selected_strings(lines, pattern):
    return "\n".join(sorted({s for s in lines if re.search(pattern, s)}))


def collect_ios(args):
    app = args.app
    info = plistlib.loads((app / "Info.plist").read_bytes())
    binary = app / info["CFBundleExecutable"]
    code, out, err = run("codesign", "-dvvv", str(app))
    if code:
        raise RuntimeError(err)
    display = "\n".join(s for s in (out + err).splitlines() if not s.startswith("Executable="))
    verify, vo, ve = run("codesign", "--verify", "--deep", "--strict", str(app))
    validation = (vo + ve).replace(str(app), app.name)
    load = checked("xcrun", "otool", "-l", str(binary)).splitlines()
    encryption = []
    for i, line in enumerate(load):
        if "cmd LC_ENCRYPTION_INFO" in line:
            encryption.extend(load[i:i + 6])
    write(args.output, "01-provenance.txt", f"# IPA sha256\n{digest(args.ipa)}  {args.ipa.name}\n\n"
          f"# codesign -dvvv (metadata display, NOT integrity verification)\n{display}\n\n"
          f"# codesign --verify --deep --strict\nexit_code={verify}\n{validation}\n"
          f"# Mach-O encryption load command\n" + "\n".join(encryption))
    keys = {k: v for k, v in info.items() if k.endswith("UsageDescription") or k in {
        "CFBundleIdentifier", "CFBundleShortVersionString", "CFBundleVersion", "CFBuildDate",
        "FBAppVersion", "MinimumOSVersion", "BGTaskSchedulerPermittedIdentifiers", "UIBackgroundModes",
        "PHPhotoLibraryPreventAutomaticLimitedAccessAlert", "FBKeychainAccessGroup"}}
    write(args.output, "02-info-plist.json", json.dumps(keys, indent=2, sort_keys=True))
    entitlements = checked("codesign", "-d", "--entitlements", ":-", str(app))
    write(args.output, "03-entitlements.json", json.dumps(plistlib.loads(entitlements.encode()), indent=2, sort_keys=True))
    strings = checked("strings", "-n", "8", str(binary)).splitlines()
    write(args.output, "04-command-names.txt", "# Exact command/event strings; registration and availability not runtime-verified.\n" +
          selected_strings(strings, r"^(home|health|photo|media|album|geofence|bluetooth|device|calendar|contacts|reminders|message|location|data_source|shortcut_notifications)\.[a-z_.]+$"))
    snippets = [s for s in strings if any(s.startswith(prefix) for prefix in [
        "Turn on to back up your camera roll.", "Turning this off fully disables camera roll sync.",
        "When true, enable the persistent full-library override", "Cancel the currently running camera roll sync.",
        "Create a geofence-triggered HomeKit bridge.", "List HomeKit accessories the user has paired",
        "Scan all reachable HomeKit accessories", "[LBR][SYNC] HealthKit provider unavailable",
        "Trigger a sync of the user's camera roll", "Share a text copy of all your Apple Notes",
        "To stop iMessage reads when the user asks to disconnect",
        "Incoming messages forwarded by a user-created Apple Shortcuts automation."])]
    write(args.output, "05-sync-and-consent.txt", "# Selected tool descriptions and UI copy from strings -n 8; not runtime observations.\n" + "\n".join(sorted(set(snippets))))
    imports = checked("xcrun", "nm", "-u", str(binary))
    health_types = sorted(set(re.findall(r"^_(HK\w*TypeIdentifier\w+)$", imports, re.M)))
    write(args.output, "11-health-import-count.txt", f"# Unique HealthKit type-identifier imports: {len(health_types)}\n"
          "# Imports are not a list of granted permissions or demonstrated uploads.\n" + "\n".join(health_types))
    extensions = []
    for extension in sorted((app / "PlugIns").glob("*.appex")):
        metadata = plistlib.loads((extension / "Info.plist").read_bytes())
        extensions.append({"bundle": extension.name, "identifier": metadata.get("CFBundleIdentifier"),
                           "extension": metadata.get("NSExtension")})
    write(args.output, "12-extension-metadata.json", json.dumps(extensions, indent=2, sort_keys=True))


def collect_android(args):
    prefix = "com/facebook/aura/"
    specs = [
        ("nodes/datasource/ProactiveSyncRunner.java", r"NodeHitlRequestKind.PROACTIVE_SYNC|nodeHitlGate.check|NodeHitlResult.Denied"),
        ("commands/notifications/NotificationsDataSource.java", r"PROACTIVE_SYNC|companion.check|isNotificationIngestionDisabled"),
        ("gateway/HatchNodeHitlGate.java", r"kind != NodeHitlRequestKind.PROACTIVE_SYNC|return denied\(nodeHitlRequest2\)|return PermissionDefaultMode.ALWAYS_ASK|baseline fetch failed"),
        ("commands/calendar/CalendarDataSource.java", r"PROACTIVE_.* =|BACKFILL_.* =|emitsProactively =|supportsBackfill =|new ProactiveTrigger.ContentObserver"),
        ("commands/notifications/HatchNotificationFilterManager.java", r"new NotificationFilter\[\]"),
        ("startup/boot/HatchBootReceiver.java", r"reregisterAll|Failed to enqueue proactive sync bootstrap|Forced notification listener rebind"),
    ]
    write(args.output, "10-review-corrections.txt", excerpts(args.sources, [(prefix + p, pattern) for p, pattern in specs]))
    permissions = (args.existing_evidence / "02-permissions.txt").read_text()
    health = sorted(set(re.findall(r"android\.permission\.health\.READ_[A-Z_]+", permissions)))
    extra = [p for p in health if p.endswith(("READ_HEALTH_DATA_HISTORY", "READ_HEALTH_DATA_IN_BACKGROUND"))]
    data = [p for p in health if p not in extra]
    write(args.output, "11-health-permission-count.txt", f"# Derived from evidence-android/02-permissions.txt\nData-category permissions: {len(data)}\n" +
          "\n".join(data) + f"\n\nAdditional access permissions: {len(extra)}\n" + "\n".join(extra))


def collect_mac(args):
    resources = args.app / "Contents/Resources"
    specs = [
        ("chrome/lib/pairing-security.js", r"https://hatch.meta.ai|https://agent.meta.ai|event.source !==|event.isTrusted !==|event.origin !==|url.protocol !== 'wss:'|isAllowedHatchWebGatewayHost\(url.hostname\)"),
        ("chrome/background.js", r"isAllowedHatchWebSender\(sender\)|Unauthorized Muse pairing sender|/api/hatch/extension-pairing"),
        ("chrome/lib/blocked-sites.js", r"function isNonWebScheme|scheme !== 'http'|malformed http\(s\) URL fails closed"),
    ]
    result = excerpts(resources, specs)
    web = (resources / "hatch/index.html").read_text()
    result += "\n\n## hatch/index.html (bounded minified snippets)\n"
    for needle in ["Wi?.autoSync.enabled??!0", "setLocalConnectorAutoSync", "function localConnectorAutoSyncRowProps"]:
        at = web.find(needle)
        if at < 0:
            raise ValueError(f"Missing expected web evidence: {needle}")
        result += web[max(0, at - 45):at + 210] + "\n"
    listeners = []
    for js in (resources / "chrome").rglob("*.js"):
        if "onMessageExternal" in js.read_text():
            listeners.append(str(js.relative_to(resources)))
    result += "\n## Literal onMessageExternal occurrences in chrome/**/*.js\n" + ("\n".join(listeners) or "No matches; this is a bounded literal search, not proof about future builds.")
    write(args.output, "12-permission-and-pairing-review.txt", result)


def collect_release(args):
    url = "https://www.facebook.com/endo/release/appcast.xml?channel=production"
    with urllib.request.urlopen(url, timeout=30) as response:
        root = ET.fromstring(response.read(1024 * 1024))
    ns = {"sparkle": "http://www.andymatuschak.org/xml-namespaces/sparkle"}
    items = []
    for item in root.findall("./channel/item"):
        enclosure = item.find("enclosure")
        items.append({"title": item.findtext("title"), "published": item.findtext("pubDate"),
                      "version": item.findtext("sparkle:shortVersionString", namespaces=ns),
                      "build": item.findtext("sparkle:version", namespaces=ns),
                      "length": enclosure.get("length") if enclosure is not None else None})
    if not items:
        raise ValueError("No release items; response may be gated or malformed")
    write(args.output, "13-release-feed.json", json.dumps({"source": url,
          "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "note": "Normalized metadata only; CDN query strings omitted. This does not verify the downloaded DMG against the feed signature.",
          "items": items}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="kind", required=True)
    ios = sub.add_parser("ios")
    ios.add_argument("ipa", type=Path)
    ios.add_argument("app", type=Path)
    ios.set_defaults(collect=collect_ios)
    android = sub.add_parser("android")
    android.add_argument("sources", type=Path, help="JADX sources directory")
    android.add_argument("existing_evidence", type=Path, help="directory containing 02-permissions.txt")
    android.set_defaults(collect=collect_android)
    mac = sub.add_parser("mac")
    mac.add_argument("app", type=Path)
    mac.set_defaults(collect=collect_mac)
    release = sub.add_parser("release")
    release.set_defaults(collect=collect_release)
    for command in [ios, android, mac, release]:
        command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.collect(args)


if __name__ == "__main__":
    main()
