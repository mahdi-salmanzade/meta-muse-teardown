# Muse for iOS (`com.facebook.hatch` 8.1.0)

The iPhone build of Meta's Muse agent. iOS keeps apps out of SMS, call logs and other apps' notifications, so Muse uses what Apple does allow: **HealthKit (110 data types), always-on location, HomeKit control of your door locks and cameras, a camera-roll uploader, and Shortcuts automations that forward your iMessages and email to Meta.**

← Back to the [main report](README.md) · Evidence: [`evidence-ios/`](evidence-ios/)

---

## 1. Authenticity: a genuine Meta binary, decrypted, not modified

The file (`com.facebook.hatch_8.1_und3fined.ipa`, sha256 `70c3cfe5bde49e31eecd087fdbb6749703d2dd74f124c7c464866884d72603b2`) is a **FairPlay-decrypted App Store dump**. "und3fined" is the dumper's tag. We checked it for tampering before trusting any of its contents ([`01-authenticity.txt`](evidence-ios/01-authenticity.txt)):

| Check | Result |
|---|---|
| Signer (all 5 Mach-O binaries) | Apple App Store chain (`Apple iPhone OS Application Signing` → `Apple iPhone Certification Authority` → `Apple Root CA`), **TeamIdentifier `V9WTTPBFK9`**, the same Meta team that signs the Mac app |
| Bundle | `com.facebook.hatch`, version 8.1.0, build `1074192126`, executable `HatchApp` |
| Encryption | `cryptid 0` in every binary (decrypted) |
| Code pages vs Apple's signed CodeDirectory | Every 4 KiB page matches **except** the decrypted pages and the single page holding `cryptid`. Setting `cryptid` back to 1 makes that page match exactly. **Load commands are exactly as signed, and no dylib was injected.** |
| Info.plist, entitlements, CodeResources | Hashes match the signature. 473 resource seals plus the nested bundles: 0 missing, 0 extra |
| Linked libraries | Only system frameworks and `@rpath/MobileConfig.framework` (Meta). No `.dylib`, Substrate, ElleKit or tweak strings |
| Foreign files | Only `Payload/decrypt.day` (9 bytes, text `und3fined`), outside the `.app` bundle and never referenced |

**Verdict:** this is Meta's App Store code. The one thing a decrypted IPA can't prove cryptographically is the decrypted instruction bytes, but nothing else in the bundle differs from what Apple signed.

## 2. Agent commands

There's a contiguous command table in the binary ([`05-agent-tools.txt`](evidence-ios/05-agent-tools.txt)). The transport is `node.register` → `node.invoke.request` / `node.invoke.result`, plus `/nodes/heartbeat`.

| Area | Commands |
|---|---|
| **Location** | `location.get`, `location.set_sharing_mode`, `geofence.set` / `list` / `remove` |
| **Health** | `health.samples`, `health.query` |
| **HomeKit** | 14 `home.*` commands incl. **`home.accessory.set`**, **`home.security.sweep`**, `home.bind_geofence` |
| **Calendar / Reminders** | `calendar.search`, `calendar.events.create/update/delete`, `reminders.*` |
| **Contacts** | `contacts.search/create/update/delete` |
| **Photos** | `photo.sync`, `media.delete`, `album.*` |
| **Other** | `bluetooth.scan`, `message.draft`, `device.find`, `data_source.backfill`, `data_source.refresh`, `ui.navigate.*` |

**Not present on iOS:** sending SMS, placing calls, camera or screen capture, reading other apps' notifications, a custom keyboard, or a VPN/network extension. iOS doesn't allow the first several, and Meta didn't ship the last two.

**Approval gate:** each command has a human-in-the-loop prompt ("{assistant} wants to…", 45 strings) with persistent **`allow_always` / `auto_allow`** options (UI: "Always allowed", "Auto allowed"). The log line `Node data sync: node HITL denied proactive sync` shows proactive syncs go through the same gate. Once you tap "Always", later requests are expected to go through without asking again (inferred, not provable statically).

## 3. Background data sync

Nine sync sources ([`06-sync-upload.txt`](evidence-ios/06-sync-upload.txt)):

```
CalendarSyncSource     ContactsSyncSource        RemindersSyncSource
HealthSyncSource       LocationSyncSource        NotesSyncSource
EmailContextSyncSource IMessageContextSyncSource HomeKitBridgeSource
```

- Chunked **backfill** of history (`chunked backfill starting fresh=`).
- Scheduled by the background task **`com.meta.hatch.nodedata.sync.refreshTask`**.
- **`HatchVmLockedSilentPushHandler`** (`hatch_node_vm_locked`): a **silent push** from Meta's server makes the app reconnect (`connectWithBootstrap`) from the background, with no user interaction.

## 4. Camera roll: the iOS version of MediaSync

`HCHHatchMediaSync` uploads through `media_sync.upload_asset`, scheduled by the background task **`com.meta.hatch.cameraroll.sync.processingTask`**.

- Sync is triggered **on launch, on foreground, when you join Wi-Fi, and whenever your photo library changes**.
- About **500 photos per run** on Wi-Fi, unless a `full_sync` sets a persistent unlimited override (**`cameraRollSyncBypassLimit`**).
- Permission prompt: *"Muse needs access to your photo library to sync media to your agent."*

Unlike Android, this is a library mirror, like the Mac build.

## 5. Health: 110 HealthKit types

Entitlements: `com.apple.developer.healthkit` + **`healthkit.background-delivery`**. `healthkit.access` is empty, so there's **no clinical-records access** ([`07-health.txt`](evidence-ios/07-health.txt)).

It imports 110 HealthKit type identifiers (`nm -u`), including heart rate, **heart-rate variability**, **AFib burden**, **blood oxygen**, **blood pressure**, **blood glucose**, **insulin delivery**, **blood alcohol**, **sleep**, **fall count**, **State of Mind** (mood logging), full **nutrition**, and **workout GPS routes**. Uploads come from `uploadSnapshot(...includeRawSamples...)` and `health.background_update`. With background delivery, iOS wakes the app when new samples arrive.

## 6. Location and HomeKit

([`08-location.txt`](evidence-ios/08-location.txt))

- `startMonitoringSignificantLocationChanges`, and `[LBR] Location change detected, sending location update` once sharing mode is **`always`**.
- The agent's instructions say "Use ONLY when the user explicitly asks" before switching to `always`.
- Geofences default to a 150 m radius. **`home.bind_geofence`** runs HomeKit actions automatically when a geofence fires.
- The `home.*` commands let the remote agent set accessories (locks, garage doors, lights) and run a **security sweep** of your home devices.

A Meta-hosted VM that knows when you leave home and can operate your door locks is a big increase in exposure.

## 7. iMessage, Mail and Notes through Shortcuts

iOS doesn't let apps read iMessage. Muse ships App Intents that **Shortcuts automations** can call without opening the app: `HCHForwardIMessageToHatchAppIntent` and `HCHForwardEmailToHatchAppIntent`. The app then **walks the user through building an automation that forwards messages to Meta**. Verbatim from the binary:

> "Leave Sender empty and type a **single space in Message Contains**. One-word texts and photos without a caption have no space, so they aren…"
> "Add them to Sender and leave Message Contains empty. **Every message they send comes through**, including one-word replies and photos."

A single space matches nearly every message. Other strings: *"Previously uploaded messages are not deleted."* and, for Notes, *"Share a text copy of all your Apple Notes."*

This gets around iOS's privacy model: Apple blocks apps from reading your messages, so Muse has **you** build the pipe.

## 8. Shared Meta identity

([`03-entitlements.txt`](evidence-ios/03-entitlements.txt), [`10-notable.txt`](evidence-ios/10-notable.txt))

- App groups **`group.com.facebook.family`** and **`group.com.metaplatforms.family`**, and keychain group `T84QZS65DQ.platformFamily`: storage shared with Facebook, Instagram, Messenger and WhatsApp on the same phone.
- `FBFamilyDeviceID` logged next to `idForVendor`, and a **`group.com.facebook.family.appgrouptokenshare`** container.
- IDFA and SKAdNetwork are imported. There's no App Tracking Transparency usage string, so IDFA will probably read as zeros.

## 9. Other notable pieces

- **"Meta SSH access"**: a setting that says *"Give temporary access… Open access to your CVM for debugging purposes"* and calls `https://api.muse.ai/ssh-access/tokens`. It grants Meta staff shell access to *your* cloud VM, where your synced data lives. It's probably limited to internal testing (the build branch string is `dev`), but it ships in the App Store binary.
- **151 unique hosts**, including `hatch.metaaivm.com`, `agent.meta.ai`, `hatch-api.meta.ai`, `api.muse.ai` and `genai-hatch-realtime.facebook.com`. Some traffic goes through **Oblivious HTTP relays** (`meta-ohttp-relay-prod.fastly-edge.com`, `meta.privacy-gateway.cloudflare.com`). This is a genuine privacy measure for the traffic it covers ([`09-endpoints.txt`](evidence-ios/09-endpoints.txt)).
- **Extensions:** Notification Service, Share (Safari `GetPageContent.js` sends only title, URL, description and selected text), and Widget. There's no keyboard and no VPN ([`04-extensions.txt`](evidence-ios/04-extensions.txt)).
- **Clean in this build:** no third-party trackers (no Firebase, AppsFlyer or Sentry), no jailbreak detection, no bot-evasion scripts. App Attest is used.

## 10. Summary

| Capability | Proven by |
|---|---|
| 110 health types, background delivery, raw-sample upload | HealthKit entitlements, `nm -u`, `uploadSnapshot(...includeRawSamples...)` |
| Always-on location + geofence-triggered actions | `startMonitoringSignificantLocationChanges`, `home.bind_geofence` |
| Remote control of door locks, cameras, lights | `home.accessory.set`, `home.security.sweep` |
| Camera roll mirrored to Meta | `HCHHatchMediaSync`, `cameraRollSyncBypassLimit`, BGTask |
| iMessage / email forwarding via Shortcuts, "single space" trick | `HCHForwardIMessageToHatchAppIntent`, in-app guidance strings |
| Calendar, contacts, reminders, notes backfill + sync | 9 `*SyncSource` classes, `data_source.backfill` |
| Server can wake the app | `HatchVmLockedSilentPushHandler` |
| Cross-app Meta identity | `group.com.facebook.family`, `FBFamilyDeviceID` |

## 11. Remove it

1. Settings → Privacy & Security → **Location Services** → Muse → **Never**.
2. **Health** app → Sharing → Apps → Muse → **Turn Off All**.
3. Settings → Muse → Photos → **None**. Also turn off Contacts, Calendars, Reminders, **Home**, Bluetooth.
4. **Shortcuts** → Automation: **delete every automation that uses "Forward … to Muse"**. Uninstalling the app doesn't delete what was already forwarded.
5. Delete the app, then request deletion through Meta's Accounts Center.

---

*Static analysis only (codesign, otool, nm, strings, page-hash verification against Apple's CodeDirectory). Nothing was installed or run. The IPA and extracted bundle are not in this repo.*
