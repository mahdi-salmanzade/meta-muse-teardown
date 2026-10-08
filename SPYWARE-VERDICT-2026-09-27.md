# Is Muse spyware? Byte-level audit — 27 September 2026

> **Dated research.** Findings below apply to the named samples and checks. For later changes and the current interpretation, see [version history](VERSIONS.md) and [research history](RESEARCH-HISTORY.md).

[Reports](README.md) · [Spyware verdict](SPYWARE-VERDICT-2026-09-27.md) · [Cross-platform](CROSS-PLATFORM.md) · [Release audit](RELEASE-AUDIT-2026-09-27.md) · [Evidence index](EVIDENCE.md) · [Findings data](evidence-updates/2026-09-27/08-spyware-audit-findings.json)

**Editorial assessment:** the author calls Muse “spyware by design” because of the breadth of cloud-agent access, retention disclosures and control weaknesses. This is a privacy judgment, not a verified malware classification. Permission denial can prevent collection. Static client paths do not prove that a particular record was uploaded, retained or used in training.

**Independent review of today's changes:** [corrections and verification](TODAYS-CHANGES-AUDIT-2026-09-27.md). The raw finder/verifier notes are retained as historical analysis, including disputed and superseded claims. Their labels are not themselves proof. No native app or Meta account was used; the separate extension tests used synthetic data and a local gateway.

The technical concerns remain: broad remote reads and background sync, potentially ambiguous historical-sharing copy, default-enabled diagnostic code, local approval gaps, browser pause/unpair behavior, and data concerning people other than the account holder. OS permissions and app approval modes are real controls. Server-held settings do not make every read inevitable, and absence of one category check does not establish absence of all consent.

## 1. Integrity: every byte accounted for

| Sample | Result |
|---|---|
| **macOS 4.1** (`Muse-4.1.dmg`, sha256 `7a407afc…74561`) | All 35,748,449 DMG bytes map to four regions with no gaps: compressed data fork (0–35,724,403), XML index (13,969 B), code signature (9,565 B) and `koly` trailer (512 B). Meta Developer ID signature valid, notarized, UDIF checksums pass. The extracted app is byte-identical to the DMG contents. All 337 entries were hashed: 317 match the sealed hashes and the rest are covered by code directories or special slots. The one exception is the 9-byte legacy `PkgInfo` (`APPLWRUN`). No appended data after any Mach-O, MP4, PNG, JPEG or DMG region. Five executables, all signed by Meta (`V9WTTPBFK9`) with hardened runtime. |
| **macOS 3.0 → 4.1** | No files added or removed. The main executable and web module changed; changed-file or tool-name inventories do not prove that all other behavior is unchanged. Sparkle, Autoupdate and Updater differ only inside signature blobs. Crashpad additionally has eight differing UUID bytes; no other helper-byte changes remain after those regions are excluded. |
| **Android 9.0.0.11.178** | Every byte of the APK is accounted for. Both embedded-certificate JWT signatures verify, and 41/44 ordinary file hashes match respectively. The special manifest digest was not independently checked. The transparency certificate differs from the APK signer; it is packaged inside the signed APK, not a separately verified trust anchor. Signing certificate `a16bbe02…` matches the 8.0 baseline. No dynamic DEX or code loading was found. |
| **iOS 8.1** (third-party decrypted IPA) | Apple's CMS signature verifies to Apple Root CA for all five binaries. Checked metadata and pages outside FairPlay ranges match signed hashes after cryptid normalization. Four nested decrypted executables mismatch the main resource seal and are checked separately. The whole-app signature remains invalid. The decrypted `__TEXT` cannot be checked, because the signed hashes cover ciphertext. FairPlay `.sinf` metadata is outside this authenticity claim; attribution of its account name or decryption time was not established. The IPA is not redistributed and the name is not published. |

## 2. How the findings were sorted

The earlier rubric tagged suspected covert collection, consent bypass, undisclosed exfiltration, persistence and remote control. Those tags describe the finders' interpretations, not proven transmission or intent. A missing Muse category check can coexist with an OS grant, prior consent or a server gate. “Gated” means a control was identified; its presence matters to whether the operation runs. Historical labels in the JSON are preserved for traceability; corrected wording below and today's independent review take precedence.

Seven finder agents were assigned: Mac data flows (it returned no results; see §6), Mac consent and defaults, the Mac remote-command approval path, every remaining Mac resource and helper binary, the 3.0→4.1 delta, the Android APK and the iOS IPA. Each of the 22 findings with a spyware angle was then attacked by two independent verifiers. One looked for the consent gate that would defeat the claim. The other re-opened the cited bytes and checked whether the code was actually wired up. Reviewer agreement is not independent runtime proof. Several findings were qualified, and today's independent audit found qualifications that the prose had omitted.

## 3. Findings that survived verification

Proof levels: **present** (code exists), **reachable** (wired into a live path), **default on**. None is marked **transmitted**, because no traffic was captured. The data paths below are built to send their data to Meta; the update, login, boot and write-command rows are about control, not upload.

### macOS 4.1

| Finding | Evidence | Status after verification |
|---|---|---|
| **Calendar, Reminders and Contacts have no in-app auto-sync switch.** The row builder returns nil for them (static set initialised at `0x10042f440`, checked at `0x1001333a4`). Their ongoing sync is decided by the resolver at `0x1001334bc`: a stored choice with no UI writer identified for them, then the MetaConfig flag `endo_rollout:featured_app_proactive_sync_enabled`, then false. Their consent text still says the data "will be automatically updated … going forward". | `Muse` `0x1001334bc`, `0x1001335a8`, `0x10042f440`; consumer `0x1001bf14c` (`EndoCalendarSyncSource`) | Potential consent/control mismatch; not a demonstrated bypass. The flag is not in the app's registered MetaConfig key list. If Meta never delivers it, these connectors resolve to **off** and the copy overpromises. If the delivered value is true, this resolver can enable sync subject to other gates; no dedicated switch was found in the reviewed UI. Delivery alone does not mean true. |
| For Notes, iMessage and Mail, the **starting position of the "Keep … up to date" switch comes from that server flag**. Connect saves whatever the switch shows, touched or not. | Same resolver; web consent dialog | Server-influenced initial selection. The switch and copy are shown before Connect; the stored user choice subsequently wins. |
| **Client telemetry is on by default.** Its only toggle sits in employee-gated internal settings. | `index.html` module: `readStoredClientTelemetryPreference()` returns true unless the stored value is `"false"` | Default-enabled diagnostic code; actual transmission and external policy disclosure untested. |
| **Crash upload code is enabled by default** to `https://www.facebook.com/mobile/ios_breakpad_crash_logs/`, with `user_id` and `session_id` annotations. The handler's enable check is hard-coded true, and no ordinary-user in-app opt-out was found in the reviewed UI. | `Muse` string at file offset `0xc58000`; provider `isEnabled` at `0x10064d288` | Default-enabled diagnostic code. No ordinary-user opt-out found in the reviewed UI; actual upload contents and policy disclosures untested. |
| **Auto-update is forced on at every launch** (12-hour checks, silent download). Sparkle's own opt-in prompt is pre-empted. | `Muse` `0x10003e070` | Automatic update preference; not proof of malicious persistence or unauthorized data collection. Updates are Ed25519-signed. |
| The **standalone browser extension can attempt pairing again when a Muse web page gains focus**. Disconnecting stores no opt-out. | `chrome/background.js` 649–676; `lib/connection.js` 141–151 | Client-side opt-out weakness. Successful re-pairing still requires the server to issue credentials; production behavior was not tested. A badge and popup are attempted after successful pairing. |
| An agent command, `media_library.sync`, turns on **persistent photo-library sync**. | Web bundle and native tool table | Gated capability. A per-command approval card plus the macOS Photos prompt stand in front of it. Weaknesses: "allow always" never expires and no photo-sync off-switch was found in the reviewed web UI; OS revocation remains available. |
| Launch at login uses the visible **"Run on startup"** toggle (`SMAppService`). No helper, LaunchAgent or daemon is embedded. | `Muse` symbols | Gated. Covert persistence was not found. |
| **Bundled Sparkle reports 2.7.0-beta.1 / 2040**, predating upstream installer-client hardening. | [Upstream release](https://github.com/sparkle-project/Sparkle/releases/tag/2.7.2), [maintainer conditions](https://github.com/sparkle-project/Sparkle/discussions/2764), [local checks](evidence-updates/2026-09-27/09-independent-verification.json) | Dependency risk requiring deployment-specific validation. No XPC service bundles ship here; the Autoupdate race requires a privileged update and package support. No exploit reproduced. |

### Android 9.0

| Finding | Evidence | Status |
|---|---|---|
| **History backfill has no app-level connection-date clamp identified.** Messages, Call Log and Health copy says "shared after you connect"; Calendar/Contacts disclose existing information. OS history limits still apply. `data_source.backfill` accepts any ISO-8601 `start_date` for SMS, call log, contacts, calendar and health. | `SmsDataSource` backfill (jadx lines 208–241); `HatchNodeClient.smali` line 3686; strings `0x7f1206df`, `0x7f1206db` | **Reachable historical-read path and possible disclosure ambiguity.** Not observed exfiltration: a prompt can show the date window, and the wording may refer to sharing time rather than record age. |
| **A server-supplied baseline decides whether reads run without a prompt.** An unset READ category resolves to ALLOW, and an unmatched wire value resolves to `AUTO_ALLOW`. With no cached baseline, it fails closed. | `PermissionDefaultMode.fromWire`, `HatchNodeHitlGate` | Server-held approval baseline with user overrides; not itself proof that a denial is bypassed. |
| **`location.get` and geofence commands have no Muse approval step.** Only the Android location permission gates them. Geofence crossings post a local notification. | `NodeHitlCatalog.forCommand` returns null | Remote control plus gated capability. Confirmed by both verifiers. |
| **Network state (SSID/BSSID) and battery have app-open publish paths**, with no mapped Muse category gate or local toggle/disclosure found in the reviewed UI. SSID/BSSID requires the fine-location permission. | `NetworkStateDataSource`, 9.0 AppOpen/TRANSIENT path | Static app-open publish path with no mapped category gate; no disclosure found in bundled UI. Server UI, policy and actual transmissions remain untested. |
| **`photos.upload`** (up to 50 per call) is behind the flag `is_nodes_media_enabled`, which defaults off. | Photo command set | Gated capability. |
| The boot receiver re-arms geofences, alarms and sync, but only on grants the user already made. | Boot/update receiver | Gated. Covert persistence was not found. |

### iOS 8.1

| Finding | Evidence | Status |
|---|---|---|
| **The reviewed successful `photo.sync` path sets `cameraRollSyncEnabled = true`**, which turns on ongoing camera-roll sync. The tool text doesn't mention this, and it lets the agent start a sync when it "needs up-to-date photo context", not only when the user asks. | `HatchApp` offsets `0x3a58dd0`, `0x3a58ec4`; closure `0x102be94a0` | Reported persistent setting side effect behind Photos and approval gates; decrypted-code interpretation, not authenticated retail runtime proof. The Photos permission and an approval card still apply. |
| **110 imported HealthKit identifiers**, with background-delivery and raw-sample-upload machinery. Imports do not establish the requested/granted type set, immediate delivery for all types, or actual upload. | Imports and tool table | Gated capability. |
| **Background location**: significant-change monitoring is enforced only after "Always" is granted. The movement threshold is server-tunable. | `0x101f96ef8` | Gated capability plus remote control. |
| Agent write commands (HomeKit, contacts, calendar, reminders, photos) are each approval-gated. Prior “allow always” decisions and server-relayed approvals are present; neither alone establishes an unauthorized approval or bypass. | Node command table | Gated capability plus remote control. |
| iMessage and Mail forwarding App Intents run without opening the app and are allowed while the device is locked. The user must have created the Shortcut. | App Intents metadata | Gated. |

## 4. What was looked for and not found

These are bounded search results, not proofs of absence. They do not change where the data it does collect ends up. They are why the conclusion rests on design, not on hidden code.

**Android 9.0**
- No screen capture (MediaProjection), no declared accessibility service, and no clipboard listener.
- The recorded DEX search found no calls to the selected TelephonyManager identifier APIs (`getImei`, `getDeviceId`, `getLine1Number`, `getSubscriberId`, `getAllCellInfo`). This does not mean phone numbers or device identifiers are absent from other app features. `READ_PHONE_STATE` is not declared.
- No DEX class-loader construction and no runtime-downloaded modules. All 41 DEX/native-library files match packaged transparency digests; separate trust of the embedded transparency key was not established.
- No SMS, contact, notification or location content was identified in the inspected analytics calls; this is not an exhaustive data-flow proof. Notification images are not uploaded: `android.picture` is only a presence check.
- No proactive data sent before the gateway attaches. Frames are dropped until then.

**iOS 8.1**
- No agent commands for camera, microphone, screen capture or clipboard.
- No IDFA access: there is no tracking-permission string, so the prompt cannot be shown.
- No reading of the Messages database. Messages arrive only through automations the user built.
- No keyboard, VPN, call-directory or credential-provider extensions. The bundled trust store holds only public web roots.

**macOS 4.1**
- No hidden LaunchAgent, daemon or privileged helper. No background-only or agent flag in `Info.plist`, and no App Transport Security exceptions.
- No restricted entitlements (endpoint security, system extension, network extension) allowed by the provisioning profile.
- No extra payload was identified by the recorded container/resource checks; byte accounting alone cannot rule out concealed content or malicious logic. The DMG has no installer scripts.
- No Meta-specific code in the Sparkle or Crashpad helpers.
- No remotely loaded replacement UI was identified. Some displayed approval text is server-supplied (`default_content`), so text changes do not always require an app update.
- The selected literal tool-name set, entitlements and reviewed consent/default paths match between 3.0 and 4.1. An unchanged name set does not establish unchanged tool behavior; the finder notes themselves report computer-control changes.

**Not covered on macOS in this round:** a review of the screen, input and computer-control tools, and a check for obfuscation or anti-debugging. The earlier report documents Accessibility and ScreenCaptureKit computer control as agent tools that need the macOS Accessibility and Screen Recording grants. This round did not re-verify them.

## 5. Corrections to earlier reports

- **CROSS-PLATFORM.md / README (Mac auto-sync default):** the web fallback `autoSync.enabled ?? true` has no effect. The real default is: stored choice, then the server flag, then false. No UI writer of a stored choice for Calendar, Reminders or Contacts was found in the reviewed paths.
- **README §4 ("missing server value falls back to auto_allow"):** true only for the web display. Native code fails closed to "requires approval" (`Muse` `0xc46220`).
- **ANDROID.md:** `location.get`, not only geofences, lacks an approval mapping. In 9.0 `network_state` fires on app open, not on boot or in the background. `android.picture` is a presence check only. `setUserEnabled` has no statically resolved caller; dynamic reachability was not established. Missing items: `libtrafficnts.so` (server flag off, radio-signal provider hard-coded off) and an exported `PerfettoTraceReceiver` with no permission.
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

**Known gaps on macOS:** two areas are missing from this round. The data-flow finder returned no results, so there is no complete inventory of Mac endpoints and payload fields; the crash, telemetry and update channels above come from other finders. The screen, input and computer-control review did not run. The Mac verdict rests on the consent, approval-path, resources and 3.0→4.1 findings. Android and iOS received broad static passes, not exhaustive end-to-end verification; native runtime behavior and decrypted iOS authenticity remain open.
