# Muse across macOS, Android and iOS

[macOS](README.md) · [Android](ANDROID.md) · [iOS](IOS.md) · [Research plan](RESEARCH-PLAN.md) · [Evidence index](EVIDENCE.md)

One table per data type: **how** each build reaches it, whether it's fetched **on request** or sent **in the background**, whether history is **backfilled**, and what **approval check** applies. Everything here comes from static analysis of the three samples. Nothing was run. Cells marked *untested* are covered by the dynamic tests in the [research plan](RESEARCH-PLAN.md).

**Legend:** 🟢 on request only · 🟠 background sync, approval-checked · 🔴 background sync, **no approval check found** · — not present in this build

---

## Summary matrix

| Data | macOS 3.0 | Android 8.0.0.21.168 | iOS 8.1.0 |
|---|---|---|---|
| **Text messages** | iMessage `chat.db` read + send (Full Disk Access); 🟠 auto-sync + backfill | SMS read + send; 🟠 proactive sync + backfill | 🟠 only what a user-built Shortcuts automation forwards; `message.draft` (user sends) |
| **WhatsApp** | 🟢 `whatsapp.search` reads `ChatStorage.sqlite`; "no background message index" | via notifications only (see below) | — |
| **Other apps' notifications** | — | 🟠 listener sees every app, **default `ALL`**; can reply / press buttons | — (iOS doesn't allow it) |
| **Email** | Mail.app via AppleScript, read/send/delete; 🟠 auto-sync of sender + subject, body on request | via notifications only | 🟠 Shortcuts forwarding intent |
| **Notes** | read/create; 🟠 auto-sync | — | 🟠 Shortcuts "text copy of all your Apple Notes" |
| **Calendar** | 🟠 auto-sync | 🟠 observer sync (−7 / +14 days), 30-day backfill chunks | 🟠 `CalendarSyncSource` |
| **Reminders** | 🟠 auto-sync | local alarms/reminders only | 🟠 `RemindersSyncSource` |
| **Contacts** | 🟠 auto-sync | 🟠 sync + backfill; create/update/delete | 🟠 `ContactsSyncSource`; create/update/delete |
| **Call history / calls** | — | 🟠 call-log sync + backfill; `phone.dial` | — |
| **Photos** | background `MediaSync` uploader | 🟢 agent-requested batches (≤50), on-device ML Kit labels | camera-roll sync (~500/run, persistent full-library override) |
| **Health** | — | 🟠 19 Health Connect types + history + background | 110 HealthKit identifiers imported; background delivery; requested set *untested* |
| **Location** | — | 🔴 **geofence crossings publish lat/long with no check**; `location.get` | always-on significant-change + geofences; `LocationSyncSource` |
| **Wi-Fi / network identity** | — | 🔴 **SSID, BSSID, carrier published with no check** | not in command table |
| **Browser** | Chrome extension: `debugger` on `<all_urls>`, history, bookmarks, downloads | — | Share extension: title / URL / description / selection |
| **Screen & input** | screen capture + Accessibility control | — | — |
| **Files** | read/write/search/upload (credential folders refused) | — | not in command table |
| **Smart home** | — | — | HomeKit: set accessories, run scenes, **security sweep**, **geofence-triggered actions** |
| **Cross-app Meta ID** | — | Family device ID, shared only with cert-checked Meta apps | `group.com.facebook.family` app groups, `FBFamilyDeviceID` |

## Approval model

| | macOS | Android | iOS |
|---|---|---|---|
| Per-command approval ("wants to…") | yes | yes, by category (`NodeHitlGroup`) | yes (45 prompt strings) |
| Persistent "always allow" | yes | yes | yes (`allow_always`, `auto_allow`) |
| Background sync goes through the check | per connector auto-sync switch | **only 6 sources** (health, contacts, calendar, call log, SMS, notifications). Location, network and battery bypass it | log shows proactive sync can be denied by the gate |
| Default when nothing is set | consent dialog initializes auto-sync to **on** (`autoSync.enabled ?? true`) | cached **server** `connector_default`; nothing cached → deny; missing server value → **`AUTO_ALLOW`** | *untested* |

## Transport, identity and persistence

| | macOS | Android | iOS |
|---|---|---|---|
| Agent location | Meta-hosted VM (`*.metaaivm.com`) | same | same |
| Survives reboot | links to Login Items settings; registration not established. Sparkle auto-update | `HatchBootReceiver` re-arms geofences, alarms, sync; forces notification-listener rebind | background tasks (`nodedata.sync.refreshTask`, `cameraroll.sync.processingTask`) |
| Server-initiated work | gateway `client.invoke` | "Execute server-initiated device commands" foreground service | silent push → reconnect (`HatchVmLockedSilentPushHandler`) |
| Signed by | Meta Developer ID, notarized | Meta cert, Google Play source stamp | Apple App Store chain, team V9WTTPBFK9 (decrypted copy; see [IOS.md](IOS.md#1-provenance-consistent-with-a-decrypted-app-store-package-not-fully-authenticated)) |

## What the code can't tell us

1. **Production defaults.** On Android the server's `connector_default` decides background sync for the six gated sources. On macOS the consent dialog falls back to on, but native state may override it.
2. **Exact payloads.** Field names are known. Actual values, sizes and history depth need traffic capture (tests D3/D4).
3. **Deletion.** The apps say forwarded messages aren't deleted when you disconnect. Cloud retention needs an account-level test (D6).
4. **iOS Health scope.** 110 identifiers are imported, but the requested set only shows on the permission sheet (D7).

*Network, telemetry and consent-copy findings (workstreams S4/S5) will be added below when complete.*
