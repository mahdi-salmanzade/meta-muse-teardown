# Muse across macOS, Android and iOS

[macOS](README.md) · [Android](ANDROID.md) · [iOS](IOS.md) · [Spyware verdict](SPYWARE-VERDICT-2026-09-27.md) · [Research plan](RESEARCH-PLAN.md) · [Evidence index](EVIDENCE.md) · [Commit audit](COMMIT-AUDIT.md)

One table per data type: **how** each build reaches it, whether it's fetched **on request** or sent **in the background**, whether history is **backfilled**, and what **approval check** applies. These tables describe the original static samples: Mac 3.0, Android 8.0 and iOS 8.1 (a third-party decrypted copy). The [27 September supplement](RELEASE-AUDIT-2026-09-27.md) covers Mac 4.1, Android 9.0 and isolated browser-extension execution, including a changed Android network-state publishing path. Corrections from the [27 September byte-level audit](SPYWARE-VERDICT-2026-09-27.md) are applied below. Native app behavior remains untested; planned tests are in the [research plan](RESEARCH-PLAN.md).

**Legend:** 🟢 on-request path identified · 🟠 background/forwarding path with consent controls indicated · 🔴 background path without a **local Muse category-gate check** · — no corresponding path established in this review. These labels mark code paths. They are not observed uploads or a full audit of gate coverage. OS grants, source settings and server policy decide when each path runs.

---

## Where it all ends up

Muse asks permission, but the permission decides **when** your data goes to Meta, not **whether** it ends up there.

The agent does not run on your device. On all three platforms it runs in a Meta-hosted VM (`*.metaaivm.com`, see [transport](#transport-identity-and-persistence)). The Mac or phone carries out its commands and reports back. So every data path in this file is built to end on Meta infrastructure ([protocol table](#one-pipe-to-a-meta-vm)):

- **What the agent reads for you** goes back as `client.invoke.result` / `node.invoke.result`: messages, SMS, contacts, calendar, call log, photos, files, screenshots, location, health, notifications and web pages.
- **What it keeps in sync** goes up as `client.data_source.publish` (background sync and backfill) and photo sync. On macOS that covers iMessage, Mail (sender and subject; body on request), Notes and the photo library, plus Calendar, Reminders and Contacts when the server flag turns their sync on. On Android it covers SMS, call log, contacts, calendar, 19 Health Connect types and notifications, with the app filter defaulting to `ALL`. On iOS it covers calendar, reminders, contacts, location, HealthKit data, the camera roll and whatever a Shortcuts automation forwards.

That is the product working as designed, not a bug.

**Once it is there**, the apps' own text says what happens to it ([retention table](#deletion-and-retention), [footers](#where-your-data-goes-per-the-apps-own-footers)):

- Disconnecting does not delete it: *"Previous data shared with {app} won't be removed unless you choose to delete it."* (iOS)
- Deleting a message does not clear it: deleted messages *"may stay in the agent's memory"*. (Android)
- It feeds Meta's AI. iOS: *"The info used for your tasks is part of your interactions with {app}, which we use to improve AI at Meta."* Android: *"All of the info from {connector} is part of your interactions with {app}, which we may use to improve AI at Meta."* The training switch falls back to **on** in client code: as the displayed value on macOS, and as `DEFAULT_ENABLED = true` on Android.
- The VM supports Meta operator shell access: the protocol carries `ssh.operator.updated`, the status of **Meta operator SSH access** to your VM, with a toggle tied to support access (`/v1/ssh/operator/enable`, `/disable`).
- Support access ends confidentiality: *"your data will no longer be confidential"*. (Android)

**The gates are weaker than they look:**

- Meta's servers steer the defaults. On macOS the starting position of the auto-sync switch comes from the server flag `endo_rollout:featured_app_proactive_sync_enabled`. On Android the server-supplied `connector_default` baseline decides whether reads run without a prompt.
- macOS Calendar, Reminders and Contacts have **no in-app auto-sync switch**. Their ongoing sync follows the server flag, off if Meta never delivers it, while their copy promises automatic updates.
- Android 9.0 `data_source.backfill` has **no lower date bound** for SMS, call log, contacts, calendar and health. The consent text says "shared after you connect".
- Android `location.get` and geofence commands have no Muse approval step. Only the OS location permission applies. In 9.0 network state (SSID/BSSID) and battery publish on app open with no approval step and no toggle.
- iOS `photo.sync` always sets `cameraRollSyncEnabled = true`, so one approved request turns on ongoing camera-roll sync.
- "Always allow" exists on all three. On macOS it is stored with no time limit, and once photo-library sync is on there is no in-app way to turn it off.
- macOS crash reports upload by default with `user_id` and `session_id`, and client telemetry is on by default. Neither has a user-facing opt-out.

**Consent is one person's.** Messages, contacts, call logs and photos describe other people. They never saw a consent screen.

**Assessment (this report's conclusion):** Muse is spyware by design. It is built for surveillance-grade collection of a person's messages, contacts, calendar, photos, health, location and notifications into Meta's servers, where the apps say it is kept and used for Meta's AI. The consent screens are the mechanism of collection, not a limit on it.

**Limits:** this static audit found no hidden or covert collection channel and did not observe live traffic. The collection runs through the channels described below, and the consent text discloses it, except for Android history backfill and Android network state noted above. Details in the [spyware verdict](SPYWARE-VERDICT-2026-09-27.md).

---

## Summary matrix

| Data | macOS 3.0 | Android 8.0.0.21.168 | iOS 8.1.0 |
|---|---|---|---|
| **Text messages** | iMessage `chat.db` read + send (Full Disk Access); 🟠 auto-sync + backfill | SMS read + send; 🟠 proactive sync + backfill (9.0: no lower date bound) | 🟠 only what a user-built Shortcuts automation forwards, including while the device is locked; `message.draft` (user sends) |
| **WhatsApp** | 🟢 `whatsapp.search` reads `ChatStorage.sqlite`; "no background message index" | via notifications only (see below) | — |
| **Other apps' notifications** | — | 🟠 app filter defaults to **`ALL`**, subject to Notification access and OS filtering; exposed actions can reply / press buttons; image bytes not sent (`android.picture` is a presence check) | — (iOS doesn't allow it) |
| **Email** | Mail.app via AppleScript, read/send/delete; 🟠 auto-sync of sender + subject, body on request | via notifications only | 🟠 Shortcuts forwarding intent |
| **Notes** | read/create; 🟠 auto-sync | — | 🟠 Shortcuts "text copy of all your Apple Notes" |
| **Calendar** | 🟠 auto-sync; no in-app switch, follows server flag | 🟠 observer sync (−7 / +14 days), 30-day backfill chunks | 🟠 `CalendarSyncSource` |
| **Reminders** | 🟠 auto-sync; no in-app switch, follows server flag | local alarms/reminders only | 🟠 `RemindersSyncSource` |
| **Contacts** | 🟠 auto-sync; no in-app switch, follows server flag | 🟠 sync + backfill; create/update/delete | 🟠 `ContactsSyncSource`; create/update/delete |
| **Call history / calls** | — | 🟠 call-log sync + backfill; `phone.dial` | — |
| **Photos** | background `MediaSync` uploader | 🟢 agent-requested batches (≤50), on-device ML Kit labels | camera-roll sync (~500/run, persistent full-library override); agent `photo.sync` always turns ongoing sync on |
| **Health** | — | 🟠 19 Health Connect types + history + background | 110 HealthKit identifiers imported; background delivery; requested set *untested* |
| **Location** | permission prompt present; local tool not established | 🔴 `location.get` (9.0 audit) and the geofence-crossing publish path carry lat/long without a Muse approval step; OS location grants required | significant-change + geofences; `LocationSyncSource`; Always permission requested |
| **Wi-Fi / network identity** | — | 🔴 SSID/BSSID/carrier publish path without the local category check; identifiers may be null; in 9.0 it fires on app open, not at boot or in the background | not in command table |
| **Browser** | Chrome extension: `debugger` on `<all_urls>`, history, bookmarks, downloads | — | Share extension: title / URL / description / selection |
| **Screen & input** | screen capture + Accessibility control | — | — |
| **Files** | read/write/search/upload (credential folders refused) | — | not in command table |
| **Smart home** | — | — | HomeKit: set accessories, run scenes, **security sweep**, **geofence-triggered actions** |
| **Cross-app Meta ID** | — | Family device ID, certificate allow-list protects the sharing interfaces | `group.com.facebook.family` app groups, `FBFamilyDeviceID` |

## Approval model

| | macOS | Android | iOS |
|---|---|---|---|
| Per-command approval ("wants to…") | approval UI/code present | category gate (`NodeHitlGroup`); not every command maps to it | 45 prompt strings; exhaustive enforcement not established |
| Persistent "always allow" | yes; stored with no time limit and no in-app revocation (traced for `media_library.sync`) | yes | yes (`allow_always`, `auto_allow`) |
| Background sync goes through the check | per-connector auto-sync switch for Notes, iMessage and Mail only. Calendar, Reminders and Contacts have **no in-app switch**; their ongoing sync follows the server flag `endo_rollout:featured_app_proactive_sync_enabled` | **only 6 sources** (health, contacts, calendar, call log, SMS, notifications). Location, network and battery have no mapping in this local gate | log shows proactive sync can be denied by the gate |
| Default when nothing is set | auto-sync: stored choice → server flag `endo_rollout:featured_app_proactive_sync_enabled` → **off**. The web fallback `autoSync.enabled ?? true` has no effect, because native always sends a value. Approval baseline: server `connector_default`; if it is unavailable, native requires approval (`Muse` `0xc46220`) | per-category preference first; otherwise cached `connector_default`; no cache → deny proactive reads; omitted/unrecognized field in a parsed response → **`AUTO_ALLOW`** | *untested* |

## Transport, identity and persistence

| | macOS | Android | iOS |
|---|---|---|---|
| Agent location | Meta-hosted VM (`*.metaaivm.com`) | same | same |
| Survives reboot | visible "Run on startup" toggle (`SMAppService`); no LaunchAgent, daemon or helper embedded. Sparkle auto-update forced on at every launch (Ed25519-signed; bundled Sparkle predates the CVE-2025-10016 fix) | `HatchBootReceiver` re-arms geofences, alarms, sync; forces notification-listener rebind | background tasks (`nodedata.sync.refreshTask`, `cameraroll.sync.processingTask`) |
| Server-initiated work | gateway `client.invoke` | "Execute server-initiated device commands" foreground service | silent push → reconnect (`HatchVmLockedSilentPushHandler`) |
| Signature / provenance | Meta Developer ID, notarized | Meta cert, Google Play source stamp | Apple App Store signing, team V9WTTPBFK9; Apple's CMS signature verifies to Apple Root CA for all 5 binaries. The decrypted `__TEXT` cannot be checked, because the signed hashes cover ciphertext (third-party decrypted copy; see [IOS.md](IOS.md#1-provenance-apple-signed-original-decrypted-by-a-third-party)) |

## What the code can't tell us

1. **Production defaults.** On Android a server-returned, user-editable `connector_default` supplies the baseline when a category has no saved override; the production value is unknown. On macOS the auto-sync default is the server flag `endo_rollout:featured_app_proactive_sync_enabled`; its production value, and whether Meta delivers it at all, are unknown. The Mac approval baseline also comes from the server.
2. **Exact payloads.** Field names are known. Actual values, sizes and history depth need traffic capture (tests D3/D4), including whether Meta's servers ever request backfill from before the connect date.
3. **Deletion.** The apps say forwarded messages aren't deleted when you disconnect. Cloud retention needs an account-level test (D6).
4. **iOS Health scope.** 110 identifiers are imported, but imports alone do not identify the requested set. A permission-sheet capture and request-call inspection can establish the set for the tested flow (D7).

## Consent, defaults and retention: what the apps say

From the apps' own UI text ([macOS](evidence/15-consent-retention-macos.txt) · [Android](evidence-android/15-consent-retention-android.txt) · [iOS](evidence-ios/15-consent-retention-ios.txt)), compared with Meta's public posts ([comparison](evidence/15-public-statements-vs-app.txt)). The app strings and public quotes were re-checked against the builds and the live pages on 2026-09-24.

### Defaults in the code

| Setting | macOS | Android | iOS |
|---|---|---|---|
| **AI training on your interactions** | server-held value (`product_improvements.get` / `.set`); the UI shows **on** while the value is loading or unavailable (`trainingEnabled ?? true`); new-account default not in client code | `HatchAiTrainingApi.DEFAULT_ENABLED = true`; response-model fallback also true; fresh-account server state untested | footer says info "we use to improve AI at Meta"; default not readable from strings |
| **Approval default** | server-supplied `connector_default` (`auto_allow` or `always_ask`). `auto_allow` is labelled **"Ask for some actions"**: *"Before every write and some read actions"*, and the server can replace that label text. Missing value → `auto_allow` in the web display only; native fails closed to "requires approval" (`Muse` `0xc46220`) | `auto_allow` when a parsed wire value is omitted/unrecognized; no-cache proactive reads fail closed | `auto_allow` / "Auto allowed" present |
| **Background sync switch** | Notes, iMessage, Mail: starting position from the server flag `endo_rollout:featured_app_proactive_sync_enabled`, else **off**; Connect saves whatever the switch shows. Calendar, Reminders, Contacts: **no switch**; sync follows the flag while their copy says they "will be automatically updated … going forward" | server `connector_default` for 6 sources; the per-source local switch defaults on and has no writer | *untested* |

The default label itself says reads are not always prompted: *"Before every write and some read actions"*. The launch post promises checks before sensitive actions. The research post also describes unprompted read-only, previously allowed or low-risk actions. Prompted or not, a read that runs returns its result to the Meta VM. [Launch](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/) · [Research](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse).

### Where your data goes, per the apps' own footers

- macOS: *"The info Muse uses for your tasks is part of your interactions with AI. The Privacy Policy explains how we use this info, including to improve AI at Meta."*
- Android local connectors: *"All of the info from {connector} is part of your interactions with {app}, which we may use to improve AI at Meta."* The Health Connect variant says the same **“may use”** (resource `0x7f1206e7`). Custom connectors say *"which we use to improve AI at Meta"* (`0x7f1205a7`).
- iOS: *"The info used for your tasks is part of your interactions with {app}, which we use to improve AI at Meta."*
- The research post describes training trajectories that include tool calls, with sanitization and an opt-out. Tool calls are how the agent reads your data. The app footers are more explicit: they name connector information, including health, as part of the interactions used to improve AI at Meta. Not tested: which raw connector records enter training. [Research](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse).

### Deletion and retention

| Statement in the app | Platform |
|---|---|
| *"Previous data shared with {app} won't be removed unless you choose to delete it."* (on disconnect) | iOS (shared copy) |
| *"Messages already shared are not deleted."* / *"Previously uploaded messages are not deleted."* | iOS (iMessage forwarding) |
| *"Messages you delete are removed from the conversation but **may stay in the agent's memory**."* | Android |
| *"Allowing access means your chats, memory, and files will be visible to support and **your data will no longer be confidential**."* | Android (support access) |
| *"Pausing … stops all activity and locks the app."* vs iOS camera roll: *"Pausing is temporary and clears the next time you open the app."* | Android / iOS |

Read together: disconnecting stops new data, but old data stays unless you choose to delete it. Deleting a message removes it from the conversation, and the app says it may stay in the agent's memory. Reset copy names chat history, files and tasks after “including”; memory is not named (the list is not exhaustive, so this alone does not show reset keeps it). Meta describes continuous VM backups. [Research](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse).

Limits: reset coverage, retention periods and treatment of training copies were not tested. D6 can test visible effects, but cannot prove backend erasure.

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

- **Meta analytics on all three platforms** (Falco / FBAnalytics, QPL, per-command loggers). Inspected event schemas cover commands, permission states and connector-toggle changes with item counts. Those schemas do not prove all telemetry excludes message content. The macOS web UI has **1,190 click-event names** and a "Client telemetry" setting that's on by default. Its only switch sits in employee-gated internal settings, so ordinary users cannot turn it off.
- **Ad attribution:** Android has a path that reads the **Google Advertising ID** and sends it as `adid` to `/hatch/attribution/report_events`, gated by a server setting. iOS contains SKAdNetwork and AdServices attribution paths. Availability and actual transmitted identifiers remain untested; attribution does not prove conversations are used for ads.
- **Crash reporting code targets Meta** and includes minidump/memory and diagnostic collectors; Android has logcat and permission-list fields. macOS 4.1 uploads crash reports by default to `https://www.facebook.com/mobile/ios_breakpad_crash_logs/` with `user_id` and `session_id` annotations; the enable check is hard-coded true and there is no in-app opt-out. Which fields are populated and what is scrubbed remain untested; iOS sanitizer classes also exist.
- **Android 9.0 network telemetry library:** `libtrafficnts.so` (Meta Traffic Network Telemetry Services, with cell-ID and BSSID structures) ships in the APK. Its server flag defaults off and Muse hard-disables the radio-signal provider.
- **Third parties:** Google (Firebase Messaging, Play services: Advertising ID, location, sign-in, ML Kit), Spotify sign-in (Android), Stripe.js at checkout and Bing/Esri/USDA map tiles (macOS web), Sparkle updates (macOS; forced on at every launch, Ed25519-signed; Sparkle/Autoupdate/Updater changed only in signature blobs between 3.0 and 4.1, and the bundled Sparkle predates the CVE-2025-10016 fix). KaTeX/Mermaid load from jsDelivr **without integrity checks** (iOS, Android). Not identified in the inspected artifacts: Crashlytics, Firebase Analytics, AppsFlyer, Adjust, Amplitude, Mixpanel, Segment.
- **Unexplained domains:** `willow606.com`, `exe.xyz` (allowed VM gateway domains) and `www.multimango.com` (macOS). Ownership unknown.
