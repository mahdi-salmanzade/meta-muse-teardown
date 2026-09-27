# Is Muse spyware? Byte-level audit — 27 September 2026

[Reports](README.md) · [Spyware verdict](SPYWARE-VERDICT-2026-09-27.md) · [Cross-platform](CROSS-PLATFORM.md) · [Release audit](RELEASE-AUDIT-2026-09-27.md) · [Evidence index](EVIDENCE.md) · [Findings data](evidence-updates/2026-09-27/08-spyware-audit-findings.json)

**Conclusion (our assessment): Muse is spyware by design.** It is built to collect a person's messages, contacts, calendar, photos, health data, location and notifications into Meta's servers. The apps' own text says that data is not removed when you disconnect unless you delete it, and that it is used to improve AI at Meta. Muse asks permission, but the permission decides **when** your data goes to Meta, not **whether** it ends up there. The consent screens are the mechanism of collection, not a limit on it.

The agent does not run on your device. It runs in a Meta-hosted VM on all three platforms. Everything it reads for you (a tool result, sent back as `client.invoke.result` or `node.invoke.result`) and everything it keeps in sync (`client.data_source.publish`, backfill, photo sync) is copied to Meta infrastructure by design. That is the product working as intended, not a bug. Every sensitive source sits behind an OS permission prompt, and most also sit behind an in-app approval. Those prompts are real, and they control timing, not destination. They are also weaker than they look: Meta's servers can steer the defaults, some consent text does not match the code, some paths have no Muse approval step, and crash reports and client telemetry are on by default with no opt-out for ordinary users. And the consent is one person's, while messages, contacts, call logs and photos describe other people.

**Limits:** this static audit found no hidden or covert collection channel and did not observe live traffic; the collection runs through the disclosed channels described below, and the consent text discloses it except where §3 says otherwise. No Muse app was launched and no Meta account was used. The audit shows what the shipped code is built to do, not that a particular user's data was sent.

## Why the permission prompt does not settle it

**1. Saying yes is the step that sends the data.** The agent is not on the device, so for it to use any of your data, a copy has to go to the Meta VM. When you approve a read, the result goes to the agent in the Meta VM (`hatch.metaaivm.com`, per-VM `metaaivm.com` hosts). When you turn on sync, new records and backfilled history go the same way through `client.data_source.publish`. The approval card and the OS prompt are where the upload starts. See the protocol table in [CROSS-PLATFORM.md](CROSS-PLATFORM.md#one-pipe-to-a-meta-vm) and [16-network-cross-platform.txt](evidence/16-network-cross-platform.txt).

**2. Once it is there, the apps say it stays and is used.** From the apps' own strings ([macOS](evidence/15-consent-retention-macos.txt) · [Android](evidence-android/15-consent-retention-android.txt) · [iOS](evidence-ios/15-consent-retention-ios.txt)):

- On disconnect: *"Previous data shared with {app} won't be removed unless you choose to delete it."* (iOS and Android)
- On deleting messages: *"Messages you delete are removed from the conversation but may stay in the agent's memory."* (Android)
- On connectors: *"Info from this connector is part of your AI interactions, which we use to improve AI at Meta."* (Android custom-connector footer `0x7f1205a7`; the iOS task footer also says "which we use to improve AI at Meta"; Android's local-connector footers say "which we may use".)
- The AI-training switch starts from on in client code: Android `HatchAiTrainingApi.DEFAULT_ENABLED = true`. On Mac the value is held on the server and the switch is shown on when no value has loaded; the server default for new accounts is not in client code.
- The protocol carries `ssh.operator.updated`, the status of **Meta operator SSH access** to your VM (`/v1/ssh/operator/enable`, `/disable`).
- On support access: *"your chats, memory, and files will be visible to support and your data will no longer be confidential."* (Android)

**3. The gates are weaker than they look.** Each item is in the tables in §3:

- **Server-steered defaults.** On Mac the starting position of the "Keep … up to date" switch for Notes, iMessage and Mail comes from the server flag `endo_rollout:featured_app_proactive_sync_enabled`. On Android a server-supplied `connector_default` baseline decides whether SMS, call-log, contacts, calendar, notification and health reads run silently when the user has not set a per-category choice.
- **History before you connected.** Android `data_source.backfill` has no lower date bound for SMS, call log, contacts, calendar and health, while the consent text says "shared after you connect".
- **No switch at all.** Mac Calendar, Reminders and Contacts have no in-app auto-sync switch. Their ongoing sync follows the server flag (off if Meta never delivers it), while their copy promises automatic updates.
- **Approvals that never end.** On Mac, "allow always" has no time limit, and no in-app control to turn photo sync off was found in the 4.1 web bundle.
- **Paths with no Muse approval step.** Android `location.get` and geofence commands are gated only by the OS location permission. Android network state (SSID/BSSID) and battery publish on app open with no approval step, no toggle and no in-app disclosure.
- **One request becomes ongoing sync.** iOS `photo.sync` always sets `cameraRollSyncEnabled = true`, which turns on ongoing camera-roll sync.
- **Default-on channels with no opt-out.** Mac crash reports upload by default to `facebook.com` with `user_id` and `session_id`, and Mac client telemetry is on by default. Neither has an in-app opt-out for ordinary users.

**4. The consent is one person's.** Messages, contacts, call logs and photos describe other people. The person who taps Allow agrees for them. The people in the threads, the address book, the call log and the photos are not asked.

So the existence of a prompt does not answer the question. What matters is what happens after it, and the apps' own code and text answer that: the data goes to Meta, stays there after you disconnect unless you delete it, and, in the apps' words, is part of "your AI interactions, which we use to improve AI at Meta"; the apps point to Settings to manage this.

## 1. Integrity: every byte accounted for

| Sample | Result |
|---|---|
| **macOS 4.1** (`Muse-4.1.dmg`, sha256 `7a407afc…74561`) | All 35,748,449 DMG bytes map to four regions with no gaps: compressed data fork (0–35,724,403), XML index (13,969 B), code signature (9,565 B) and `koly` trailer (512 B). Meta Developer ID signature valid, notarized, UDIF checksums pass. The extracted app is byte-identical to the DMG contents. All 337 entries were hashed: 317 match the sealed hashes and the rest are covered by code directories or special slots. The one exception is the 9-byte legacy `PkgInfo` (`APPLWRUN`). No appended data after any Mach-O, MP4, PNG, JPEG or DMG region. Five executables, all signed by Meta (`V9WTTPBFK9`) with hardened runtime. |
| **macOS 3.0 → 4.1** | No files added or removed. Only the main `Muse` binary and the web module changed in function. Sparkle, Autoupdate, Updater and the Crashpad handler differ only inside their signature blobs. |
| **Android 9.0.0.11.178** | Every byte of the APK is accounted for. Both code-transparency JWTs verify (41/41 and 44/44 files). Signing certificate `a16bbe02…` matches the 8.0 baseline. No dynamic DEX or code loading was found. |
| **iOS 8.1** (third-party decrypted IPA) | Apple's CMS signature verifies to Apple Root CA for all five binaries. Headers, load commands, entitlements and resources are Apple-signed originals. The decrypted `__TEXT` cannot be checked, because the signed hashes cover ciphertext. The FairPlay `.sinf` files were rewritten by whoever decrypted the file and contain that person's account display name. The IPA is not redistributed and the name is not published. |

## 2. How the findings were sorted

The rubric sorts each finding by **how** the collection happens. It does not decide **whether** data reaches Meta; the architecture decides that (see above). A finding is tagged **covert collection** (without the user's knowledge), **consent bypass** (collection that skips or pre-empts the consent the UI implies, including server-enabled or default-on collection), **undisclosed exfiltration**, **covert persistence** or **unapproved remote control**. A powerful capability with a real prompt in front of it is tagged **gated**. Gated does not mean the data stays on the device: once the user says yes, a gated data source is built to send its results to the Meta VM like any other. A flaw that is not evidence of intent is tagged **security weakness**.

Seven finder agents were assigned: Mac data flows (it returned no results; see §6), Mac consent and defaults, the Mac remote-command approval path, every remaining Mac resource and helper binary, the 3.0→4.1 delta, the Android APK and the iOS IPA. Each of the 22 findings with a spyware angle was then attacked by two independent verifiers. One looked for the consent gate that would defeat the claim. The other re-opened the cited bytes and checked whether the code was actually wired up. No finding was refuted by both. Several were downgraded, and the corrected claims are the ones shown below.

## 3. Findings that survived verification

Proof levels: **present** (code exists), **reachable** (wired into a live path), **default on**. None is marked **transmitted**, because no traffic was captured. The data paths below are built to send their data to Meta; the update, login, boot and write-command rows are about control, not upload.

### macOS 4.1

| Finding | Evidence | Status after verification |
|---|---|---|
| **Calendar, Reminders and Contacts have no in-app auto-sync switch.** The row builder returns nil for them (static set initialised at `0x10042f440`, checked at `0x1001333a4`). Their ongoing sync is decided by the resolver at `0x1001334bc`: a stored choice that can never be written for them, then the MetaConfig flag `endo_rollout:featured_app_proactive_sync_enabled`, then false. Their consent text still says the data "will be automatically updated … going forward". | `Muse` `0x1001334bc`, `0x1001335a8`, `0x10042f440`; consumer `0x1001bf14c` (`EndoCalendarSyncSource`) | Consent bypass, qualified. The flag is not in the app's registered MetaConfig key list. If Meta never delivers it, these connectors resolve to **off** and the copy overpromises. If it is delivered, users have no in-app control over it. |
| For Notes, iMessage and Mail, the **starting position of the "Keep … up to date" switch comes from that server flag**. Connect saves whatever the switch shows, touched or not. | Same resolver; web consent dialog | Consent bypass (weak form). The switch and its copy are shown before Connect. |
| **Client telemetry is on by default.** Its only toggle sits in employee-gated internal settings. | `index.html` module: `readStoredClientTelemetryPreference()` returns true unless the stored value is `"false"` | Consent bypass (default on). |
| **Crash reports upload by default** to `https://www.facebook.com/mobile/ios_breakpad_crash_logs/`, with `user_id` and `session_id` annotations. The handler's enable check is hard-coded true, and there is no in-app opt-out. | `Muse` string at file offset `0xc58000`; provider `isEnabled` at `0x10064d288` | Consent bypass (default on). Downgraded from undisclosed exfiltration, because crash reporting is a conventional channel. |
| **Auto-update is forced on at every launch** (12-hour checks, silent download). Sparkle's own opt-in prompt is pre-empted. | `Muse` `0x10003e070` | Gated capability plus weak consent bypass. Updates are Ed25519-signed. |
| The **browser extension re-pairs when the Muse web page gains focus**. Disconnecting stores no opt-out. | `chrome/background.js` 649–676; `lib/connection.js` 141–151 | Narrow consent bypass plus security weakness. A green badge and popup appear afterwards. |
| An agent command, `media_library.sync`, turns on **persistent photo-library sync**. | Web bundle and native tool table | Gated capability. A per-command approval card plus the macOS Photos prompt stand in front of it. Weaknesses: "allow always" never expires and there is no in-app revocation. |
| Launch at login uses the visible **"Run on startup"** toggle (`SMAppService`). No helper, LaunchAgent or daemon is embedded. | `Muse` symbols | Gated. Covert persistence was not found. |
| **Bundled Sparkle is an unreleased mid-2024 snapshot** that predates upstream's installer hardening (the CVE-2025-10016 fix). | Sparkle binary compared with upstream releases | Security weakness. |

### Android 9.0

| Finding | Evidence | Status |
|---|---|---|
| **History backfill has no lower date bound**, while the consent text says "shared after you connect". `data_source.backfill` accepts any ISO-8601 `start_date` for SMS, call log, contacts, calendar and health. | `SmsDataSource` backfill (jadx lines 208–241); `HatchNodeClient.smali` line 3686; strings `0x7f1206df`, `0x7f1206db` | **Undisclosed exfiltration. Confirmed by both verifiers.** |
| **A server-supplied baseline decides whether reads run without a prompt.** An unset READ category resolves to ALLOW, and an unmatched wire value resolves to `AUTO_ALLOW`. With no cached baseline, it fails closed. | `PermissionDefaultMode.fromWire`, `HatchNodeHitlGate` | Consent bypass plus gated capability. |
| **`location.get` and geofence commands have no Muse approval step.** Only the Android location permission gates them. Geofence crossings post a local notification. | `NodeHitlCatalog.forCommand` returns null | Remote control plus gated capability. Confirmed by both verifiers. |
| **Network state (SSID/BSSID) and battery publish on app open**, with no approval step, no toggle and no in-app disclosure. SSID/BSSID requires the fine-location permission. | `NetworkStateDataSource`, 9.0 AppOpen/TRANSIENT path | Undisclosed exfiltration plus consent bypass. |
| **`photos.upload`** (up to 50 per call) is behind the flag `is_nodes_media_enabled`, which defaults off. | Photo command set | Gated capability. |
| The boot receiver re-arms geofences, alarms and sync, but only on grants the user already made. | Boot/update receiver | Gated. Covert persistence was not found. |

### iOS 8.1

| Finding | Evidence | Status |
|---|---|---|
| **`photo.sync` always sets `cameraRollSyncEnabled = true`**, which turns on ongoing camera-roll sync. The tool text doesn't mention this, and it lets the agent start a sync when it "needs up-to-date photo context", not only when the user asks. | `HatchApp` offsets `0x3a58dd0`, `0x3a58ec4`; closure `0x102be94a0` | Remote control, gated capability, consent bypass and security weakness. The Photos permission and an approval card still apply. |
| **110 HealthKit types with immediate background delivery**; raw samples are uploaded once connected. | Imports and tool table | Gated capability. |
| **Background location**: significant-change monitoring is enforced only after "Always" is granted. The movement threshold is server-tunable. | `0x101f96ef8` | Gated capability plus remote control. |
| Agent write commands (HomeKit, contacts, calendar, reminders, photos) are each approval-gated. The gate is weakened by "allow always" and by approvals relayed from the server. | Node command table | Gated capability plus remote control. |
| iMessage and Mail forwarding App Intents run without opening the app and are allowed while the device is locked. The user must have created the Shortcut. | App Intents metadata | Gated. |

## 4. What was looked for and not found

These negative results narrow what Muse does. They do not change where the data it does collect ends up. They are why the conclusion rests on design, not on hidden code.

**Android 9.0**
- No screen capture (MediaProjection), no declared accessibility service, and no clipboard listener.
- Zero references to IMEI, device ID, phone number or subscriber ID in any DEX. `READ_PHONE_STATE` is not declared.
- No DEX class-loader construction and no runtime-downloaded modules. Every code file is covered by Meta-signed code transparency.
- No SMS, contact, notification or location content leaking into analytics. Notification images are not uploaded: `android.picture` is only a presence check.
- No proactive data sent before the gateway attaches. Frames are dropped until then.

**iOS 8.1**
- No agent commands for camera, microphone, screen capture or clipboard.
- No IDFA access: there is no tracking-permission string, so the prompt cannot be shown.
- No reading of the Messages database. Messages arrive only through automations the user built.
- No keyboard, VPN, call-directory or credential-provider extensions. The bundled trust store holds only public web roots.

**macOS 4.1**
- No hidden LaunchAgent, daemon or privileged helper. No background-only or agent flag in `Info.plist`, and no App Transport Security exceptions.
- No restricted entitlements (endpoint security, system extension, network extension) allowed by the provisioning profile.
- No hidden payloads in media, fonts, icons, language packs, `Assets.car`, the Lottie JSON or `markdown-editor.html`. The DMG has no installer scripts.
- No Meta-specific code in the Sparkle or Crashpad helpers.
- No remotely loaded UI that could change the consent text without a signed update.
- No change to any tool, sync source, entitlement, consent text or consent default between 3.0 and 4.1. There are 98 tool names in each version.

**Not covered on macOS in this round:** a review of the screen, input and computer-control tools, and a check for obfuscation or anti-debugging. The earlier report documents Accessibility and ScreenCaptureKit computer control as agent tools that need the macOS Accessibility and Screen Recording grants. This round did not re-verify them.

## 5. Corrections to earlier reports

- **CROSS-PLATFORM.md / README (Mac auto-sync default):** the web fallback `autoSync.enabled ?? true` has no effect. The real default is: stored choice, then the server flag, then false. Calendar, Reminders and Contacts never get a stored choice.
- **README §4 ("missing server value falls back to auto_allow"):** true only for the web display. Native code fails closed to "requires approval" (`Muse` `0xc46220`).
- **ANDROID.md:** `location.get`, not only geofences, lacks an approval mapping. In 9.0 `network_state` fires on app open, not on boot or in the background. `android.picture` is a presence check only. `setUserEnabled` is dead code. Missing items: `libtrafficnts.so` (server flag off, radio-signal provider hard-coded off) and an exported `PerfettoTraceReceiver` with no permission.
- **IOS.md:** "signature verification fails" understates it, because Apple's CMS verifies. "Proven uploads location" is static presence only.
- **RELEASE-AUDIT §4:** Sparkle, Autoupdate and Updater changed only inside their signature blobs.

## 6. What static analysis cannot settle

These open questions bear on how much is collected and under which defaults. They do not change where collected data goes.

1. The production values of `connector_default`, `endo_rollout:featured_app_proactive_sync_enabled`, `node_hitl_enabled` and `is_nodes_media_enabled`, and whether the Mac flag is delivered at all.
2. Whether reads run without a prompt on a fresh install, per connector.
3. Whether Meta's servers ever request backfill from before the connect date.
4. Live confirmation that the data above is sent, how much and to which hosts. The protocol is built to carry it to the Meta VM; no traffic was captured.
5. Whether any Mac remote command runs with no per-action approval. A type named `EndoNodeAllowAllHITLGating` ships in 4.1 and its use was not traced. Approvals can also come back from the server already decided. Only `files.list` states in its own description that it needs no approval.
6. The default approval mode per connector on Mac and iOS. The native default routine could not be decoded statically.

These need a throwaway account and captured traffic on a test device. That is the pending phase in [RESEARCH-PLAN.md](RESEARCH-PLAN.md).

**Known gaps on macOS:** two areas are missing from this round. The data-flow finder returned no results, so there is no complete inventory of Mac endpoints and payload fields; the crash, telemetry and update channels above come from other finders. The screen, input and computer-control review did not run. The Mac verdict rests on the consent, approval-path, resources and 3.0→4.1 findings. Android and iOS were covered end to end.
