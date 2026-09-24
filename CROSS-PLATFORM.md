# Muse across macOS, Android and iOS

[macOS](README.md) · [Android](ANDROID.md) · [iOS](IOS.md) · [Research plan](RESEARCH-PLAN.md) · [Evidence index](EVIDENCE.md) · [Commit audit](COMMIT-AUDIT.md)

One table per data type: **how** each build reaches it, whether it's fetched **on request** or sent **in the background**, whether history is **backfilled**, and what **approval check** applies. Everything here comes from static analysis of the three samples. Nothing was run. Cells marked *untested* are covered by the dynamic tests in the [research plan](RESEARCH-PLAN.md).

**Legend:** 🟢 on-request path identified · 🟠 background/forwarding path with consent controls indicated · 🔴 background path without a **local Muse category-gate check** · — no corresponding path established in this review. These labels do not prove successful uploads or complete gate coverage. OS grants, source settings, server policy and runtime state still matter.

---

## Summary matrix

| Data | macOS 3.0 | Android 8.0.0.21.168 | iOS 8.1.0 |
|---|---|---|---|
| **Text messages** | iMessage `chat.db` read + send (Full Disk Access); 🟠 auto-sync + backfill | SMS read + send; 🟠 proactive sync + backfill | 🟠 only what a user-built Shortcuts automation forwards; `message.draft` (user sends) |
| **WhatsApp** | 🟢 `whatsapp.search` reads `ChatStorage.sqlite`; "no background message index" | via notifications only (see below) | — |
| **Other apps' notifications** | — | 🟠 app filter defaults to **`ALL`**, subject to Notification access and OS filtering; exposed actions can reply / press buttons | — (iOS doesn't allow it) |
| **Email** | Mail.app via AppleScript, read/send/delete; 🟠 auto-sync of sender + subject, body on request | via notifications only | 🟠 Shortcuts forwarding intent |
| **Notes** | read/create; 🟠 auto-sync | — | 🟠 Shortcuts "text copy of all your Apple Notes" |
| **Calendar** | 🟠 auto-sync | 🟠 observer sync (−7 / +14 days), 30-day backfill chunks | 🟠 `CalendarSyncSource` |
| **Reminders** | 🟠 auto-sync | local alarms/reminders only | 🟠 `RemindersSyncSource` |
| **Contacts** | 🟠 auto-sync | 🟠 sync + backfill; create/update/delete | 🟠 `ContactsSyncSource`; create/update/delete |
| **Call history / calls** | — | 🟠 call-log sync + backfill; `phone.dial` | — |
| **Photos** | background `MediaSync` uploader | 🟢 agent-requested batches (≤50), on-device ML Kit labels | camera-roll sync (~500/run, persistent full-library override) |
| **Health** | — | 🟠 19 Health Connect types + history + background | 110 HealthKit identifiers imported; background delivery; requested set *untested* |
| **Location** | permission prompt present; local tool not established | 🔴 geofence-crossing publish path carries lat/long without the local category check; OS grants required | significant-change + geofences; `LocationSyncSource`; Always permission requested |
| **Wi-Fi / network identity** | — | 🔴 SSID/BSSID/carrier publish path without the local category check; identifiers may be null | not in command table |
| **Browser** | Chrome extension: `debugger` on `<all_urls>`, history, bookmarks, downloads | — | Share extension: title / URL / description / selection |
| **Screen & input** | screen capture + Accessibility control | — | — |
| **Files** | read/write/search/upload (credential folders refused) | — | not in command table |
| **Smart home** | — | — | HomeKit: set accessories, run scenes, **security sweep**, **geofence-triggered actions** |
| **Cross-app Meta ID** | — | Family device ID, certificate allow-list protects the sharing interfaces | `group.com.facebook.family` app groups, `FBFamilyDeviceID` |

## Approval model

| | macOS | Android | iOS |
|---|---|---|---|
| Per-command approval ("wants to…") | approval UI/code present | category gate (`NodeHitlGroup`); not every command maps to it | 45 prompt strings; exhaustive enforcement not established |
| Persistent "always allow" | yes | yes | yes (`allow_always`, `auto_allow`) |
| Background sync goes through the check | per connector auto-sync switch | **only 6 sources** (health, contacts, calendar, call log, SMS, notifications). Location, network and battery have no mapping in this local gate | log shows proactive sync can be denied by the gate |
| Default when nothing is set | consent dialog initializes auto-sync to **on** (`autoSync.enabled ?? true`) | per-category preference first; otherwise cached `connector_default`; no cache → deny proactive reads; omitted/unrecognized field in a parsed response → **`AUTO_ALLOW`** | *untested* |

## Transport, identity and persistence

| | macOS | Android | iOS |
|---|---|---|---|
| Agent location | Meta-hosted VM (`*.metaaivm.com`) | same | same |
| Survives reboot | links to Login Items settings; registration not established. Sparkle auto-update | `HatchBootReceiver` re-arms geofences, alarms, sync; forces notification-listener rebind | background tasks (`nodedata.sync.refreshTask`, `cameraroll.sync.processingTask`) |
| Server-initiated work | gateway `client.invoke` | "Execute server-initiated device commands" foreground service | silent push → reconnect (`HatchVmLockedSilentPushHandler`) |
| Signature / provenance | Meta Developer ID, notarized | Meta cert, Google Play source stamp | Apple App Store signing metadata, team V9WTTPBFK9; integrity verification **fails** (consistent with decrypted copy; see [IOS.md](IOS.md#1-provenance-consistent-with-a-decrypted-app-store-package-not-fully-authenticated)) |

## What the code can't tell us

1. **Production defaults.** On Android a server-returned, user-editable `connector_default` supplies the baseline when a category has no saved override; the production value is unknown. On macOS the consent dialog falls back to on, but native state may override it.
2. **Exact payloads.** Field names are known. Actual values, sizes and history depth need traffic capture (tests D3/D4).
3. **Deletion.** The apps say forwarded messages aren't deleted when you disconnect. Cloud retention needs an account-level test (D6).
4. **iOS Health scope.** 110 identifiers are imported, but imports alone do not identify the requested set. A permission-sheet capture and request-call inspection can establish the set for the tested flow (D7).

## Consent, defaults and retention: what the apps say

From the apps' own UI text ([macOS](evidence/15-consent-retention-macos.txt) · [Android](evidence-android/15-consent-retention-android.txt) · [iOS](evidence-ios/15-consent-retention-ios.txt)), compared with Meta's public posts ([comparison](evidence/15-public-statements-vs-app.txt)). The app strings and public quotes were re-checked against the builds and the live pages on 2026-09-24.

### Defaults in the code

| Setting | macOS | Android | iOS |
|---|---|---|---|
| **AI training on your interactions** | `trainingEnabled ?? !0` → UI fallback **on** when the value is absent | `HatchAiTrainingApi.DEFAULT_ENABLED = true`; response-model fallback also true; fresh-account server state untested | footer says info "we use to improve AI at Meta"; default not readable from strings |
| **Approval default** | `auto_allow`, labelled **"Ask for some actions"**: *"Before every write and some read actions"*. Missing value → `auto_allow` | `auto_allow` when a parsed wire value is omitted/unrecognized; no-cache proactive reads fail closed | `auto_allow` / "Auto allowed" present |
| **Background sync switch** | consent dialog falls back to **on** | server `connector_default` for 6 sources | *untested* |

The launch post promises checks before sensitive actions. The research post also describes unprompted read-only, previously allowed or low-risk actions. The app's default label is consistent with that distinction; a UI label does not prove every write is freshly prompted. [Launch](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/) · [Research](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse).

### Where your data goes, per the apps' own footers

- Android has generic connector copy saying its information forms part of AI interactions used to improve AI at Meta. The Health Connect variant says **“may use”** (resource `0x7f1206e7`).
- iOS has a corresponding task-data footer.
- The research post describes training trajectories that include tool calls, with sanitization and an opt-out. The app footers are more explicit about connector information, including health. This does **not** establish that all raw connector records enter training, or that connector-derived data was excluded from the public description. [Research](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse).

### Deletion and retention

| Statement in the app | Platform |
|---|---|
| *"Previous data shared with {app} won't be removed unless you choose to delete it."* (on disconnect) | iOS (shared copy) |
| *"Messages already shared are not deleted."* / *"Previously uploaded messages are not deleted."* | iOS (iMessage forwarding) |
| *"Messages you delete are removed from the conversation but **may stay in the agent's memory**."* | Android |
| *"Allowing access means your chats, memory, and files will be visible to support and **your data will no longer be confidential**."* | Android (support access) |
| *"Pausing … stops all activity and locks the app."* vs iOS camera roll: *"Pausing is temporary and clears the next time you open the app."* | Android / iOS |

The disconnect copy says previously shared data remains unless separately deleted. Message deletion **may** leave information in agent memory; it does not establish that every deleted message persists. Reset copy names chat history, files and tasks after “including”, which is a non-exhaustive list: omission of memory is **not proof** that reset preserves it. Meta describes continuous VM backups. Backup existence alone is compatible with eventual deletion; reset coverage, retention periods and treatment of training copies remain unverified. D6 can test visible effects, but cannot prove backend erasure. [Research](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse).

## Network, protocol and telemetry

From [`16-network-cross-platform.txt`](evidence/16-network-cross-platform.txt) and the per-platform files ([macOS](evidence/16-network-macos.txt) · [Android](evidence-android/16-network-android.txt) · [iOS](evidence-ios/16-network-ios.txt)). The headline items below were re-checked against the builds.

### One pipe to a Meta VM

All three samples contain VM-gateway WebSocket/Noise support, including `hatch.metaaivm.com/v1/noise` and `Noise_XX_25519_AESGCM_SHA256`. The selected endpoint and transport depend on lease/configuration state; this is not an observation of every connection. Two protocol generations coexist: `node.*` (Chrome extension; also in the macOS and iOS apps) and `client.*` (macOS app and Android).

| Direction | Messages | Carries user data? |
|---|---|---|
| device → Meta | `client.invoke.result` / `node.invoke.result` | **yes**: results of supported commands (messages, SMS, contacts, calendar, call log, photos, files, screenshots, location, health, notifications, web pages) |
| device → Meta | `client.data_source.publish` | **yes**: background sync and backfill. Android targets **1 MiB per chunk**; **256 chunks and 64 MiB total are warning thresholds, not hard limits**. The emitter logs and continues; a separate 4 MiB wire-size check rejects oversized frames |
| device → Meta | `chat.*`, photo sync | yes |
| device → Meta | `client.register_capabilities`, `node.register` | metadata: device model, **which OS permissions you've granted** |
| Meta → device | `client.invoke` / `node.invoke.request` | commands, including `data_source.backfill` |
| Meta → device | `ssh.operator.updated` | status of **Meta operator SSH access** to your VM (`/v1/ssh/operator/enable`, `/disable`) |

### Transport security

| | macOS | Android | iOS |
|---|---|---|---|
| Certificate pinning | a "Facebook Rootcanal Prod Root CA" is embedded (role unclear) | platform config pins a **listed set of Meta domains** (`facebook.com`, `meta.com`, `instagram.com`…; 18 pins, expire 2027-09-17). **`meta.ai`, `metaaivm.com` and `muse.ai` aren't pinned there**, and `base-config` allows cleartext. Meta's native HTTP stack may apply its own pins | bundles 143 CA roots; active trust-store selection unverified |
| VM attestation (AMD SEV-SNP) | server-flagged; web default `attestation_enforce_mode = 0` ("Off"); an accept-all verifier class exists | server-flagged | server-flagged; accept-all verifier class exists; embedded Sigstore root lists **`rekor.sigstage.dev`**; active root selection and server contact unverified |
| Privacy relay (OHTTP) | anonymous VM lease path identified; web flag fallback off; shared OHTTP support also present | lease path plus shared GraphQL support; query configuration says `ALL`, runtime routing unknown | lease path plus allow-listed GraphQL support; runtime selection unknown |

The static evidence does **not** limit OHTTP to VM leasing: the mobile stacks also include GraphQL routing support. Authenticated gateway and upload paths are present, but finding account credentials alone does not establish whether a request uses a privacy relay. Runtime routing and what each intermediary learns remain untested.

**TLS interception on the VM.** The VM's outbound-network settings have a switch (`mitmMode`). On: *"All TLS connections are always intercepted for inspection."* Off: *"TLS connections are only intercepted when required by policy."* This describes a VM policy capable of inspecting the agent's outbound HTTPS, including policy-required inspection with the toggle off. The live policy and actual interception were not tested; it does not describe all traffic from the user's device.

### Telemetry, ads and third parties

- **Meta analytics on all three platforms** (Falco / FBAnalytics, QPL, per-command loggers). Inspected event schemas cover commands, permission states and connector-toggle changes with item counts. Those schemas do not prove all telemetry excludes message content. The macOS web UI has **1,190 click-event names** and a "Client telemetry" setting that's on by default.
- **Ad attribution:** Android has a path that reads the **Google Advertising ID** and sends it as `adid` to `/hatch/attribution/report_events`, gated by a server setting. iOS contains SKAdNetwork and AdServices attribution paths. Availability and actual transmitted identifiers remain untested; attribution does not prove conversations are used for ads.
- **Crash reporting code targets Meta** and includes minidump/memory and diagnostic collectors; Android has logcat and permission-list fields. Which fields are populated and what is scrubbed remain untested; iOS sanitizer classes also exist.
- **Third parties:** Google (Firebase Messaging, Play services: Advertising ID, location, sign-in, ML Kit), Spotify sign-in (Android), Stripe.js at checkout and Bing/Esri/USDA map tiles (macOS web), Sparkle updates (macOS). KaTeX/Mermaid load from jsDelivr **without integrity checks** (iOS, Android). Not identified in the inspected artifacts: Crashlytics, Firebase Analytics, AppsFlyer, Adjust, Amplitude, Mixpanel, Segment.
- **Unexplained domains:** `willow606.com`, `exe.xyz` (allowed VM gateway domains) and `www.multimango.com` (macOS). Ownership unknown.

