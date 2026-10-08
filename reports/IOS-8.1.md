> **Historical snapshot, preserved 8 October 2026.** This is the detailed report before the documentation restructure. Its version-specific findings and dated updates are retained for traceability; it is not a description of every current build. Start with the [current overview](../README.md), [platform guides](../VERSIONS.md), or [research history](../RESEARCH-HISTORY.md).

# Muse for iOS (`com.facebook.hatch` 8.1.0)

[**iOS**](../IOS.md) · [**macOS**](../README.md) · [**Android**](../ANDROID.md) · [**Spyware verdict**](../SPYWARE-VERDICT-2026-09-27.md) · [**All evidence**](../EVIDENCE.md)

**The inspected iOS sample contains command, sync and forwarding paths to a Meta-hosted VM.** OS grants and Muse approval modes can prevent access. Allowed operations may send selected results through `node.invoke.result`, `client.data_source.publish` or `media_sync.upload_asset`; this is static code evidence, not captured traffic.

Key concerns include the reported persistent camera-roll setting change in `photo.sync`, background-location paths, health-sync machinery, and user-created Shortcuts forwarding other people's messages. App copy says disconnecting does not remove previously shared data and discusses AI improvement and support access. It does not prove the retention or training treatment of a particular record.

The author's “spyware by design” wording is an editorial privacy assessment. Neither covert collection nor inevitable upload is established. [Today's verification](../TODAYS-CHANGES-AUDIT-2026-09-27.md) also identifies a missing `processing` background mode and preserves the distinction between signed metadata and unauthenticated decrypted instructions.

> **v9 update (9.1.0, [6 Oct 2026](../V9-AUDIT-2026-10-06.md)):** this page covers 8.1. The decrypted 9.1 sample adds Alo live-voice and wearable-recording code, while the identified Notes-export literals disappear. Selected collection-command names remain present; this does not establish an unchanged implementation. Decrypted code remains unauthenticated, and no upload was observed. See the [independent review](../TODAYS-CHANGES-AUDIT-2026-10-06.md).

**Sample:** a third-party decrypted 8.1 IPA; Apple's signatures authenticate code directories and checked metadata/resource hashes, but decrypted instructions and the whole app do not pass integrity verification ([§1](#1-provenance-apple-signed-original-decrypted-by-a-third-party)). The 27 September release check listed 9.0, which was not obtained or audited in that check ([release check](../RELEASE-AUDIT-2026-09-27.md#1-releases-and-provenance)).

Reviewed **2026-09-24**, corrected with the [27 September audit](../SPYWARE-VERDICT-2026-09-27.md). Nothing was installed or launched.

<a id="1-provenance-consistent-with-a-decrypted-app-store-package-not-fully-authenticated"></a>

<a id="1-provenance-apple-signed-original-decrypted-by-a-third-party"></a>

## 1. Provenance: signed metadata, unauthenticated decrypted code

| Field | Observed value |
|---|---|
| File | `com.facebook.hatch_8.1_und3fined.ipa` |
| SHA-256 | `70c3cfe5bde49e31eecd087fdbb6749703d2dd74f124c7c464866884d72603b2` |
| Bundle / version | `com.facebook.hatch`, 8.1.0, build `1074192126` |
| Internal version / build date | `8.1.0.8.136` / `2026-09-22T07:00:13` |
| Minimum OS | iOS 18.0 |
| Displayed signature metadata | Apple iPhone OS Application Signing chain; TeamIdentifier `V9WTTPBFK9` |
| Apple CMS signature | **Verifies** to Apple Root CA for all five binaries; the signed CDHashes attribute binds the sha256 CodeDirectory |
| `codesign --verify` | Fails: `invalid signature (code or signature have been modified)`, as expected once FairPlay encryption is removed |
| Main executable encryption command | `cryptid 0`, `cryptoff 16384`, `cryptsize 72089600` |

[Reproducible signature/encryption output](../evidence-ios/01-provenance.txt) · [Selected Info.plist](../evidence-ios/02-info-plist.json) · [27 September integrity check](../SPYWARE-VERDICT-2026-09-27.md#1-integrity-every-byte-accounted-for).

Independent verification confirms Apple's CMS signatures for all five binaries and their signed SHA-256 CodeDirectory binding. Altering signed content makes verification fail. After normalizing `cryptid` back to 1 for hashing only, every remaining page mismatch lies in a FairPlay range. Info.plist, requirements, resource-seal and entitlement special slots match. Ordinary sealed resource hashes match, except four nested executable hashes in the main resource seal; those executables are themselves modified/decrypted and are checked separately. The whole-app signature still fails, and this cannot rule out modifications inside decrypted ranges.

The correct claim is **authenticated metadata and matching pages outside the encrypted ranges, not authenticated decrypted code**. “Apple-signed original” was too broad for the supplied IPA. FairPlay account metadata is omitted from the published evidence. File timestamps alone cannot establish exactly when decryption happened. [Independent results](../evidence-updates/2026-09-27/09-independent-verification.json) · [reproduction script](../scripts/verify-september27-audit.py).


The [US App Store listing](https://apps.apple.com/us/app/muse-from-meta/id6760173601) independently lists Meta as the seller and version 8.1 as of the review date. Matching marketing versions do not establish byte-for-byte identity. The original IPA acquisition chain was not recorded here.

## 2. Agent commands and approval evidence

[Tool excerpts](../evidence-ios/05-agent-tools.txt) and [reproduced command/event names](../evidence-ios/04-command-names.txt) show:

| Area | Examples |
|---|---|
| Location | `location.get`, `location.set_sharing_mode`, `geofence.set/list/remove` |
| Health | `health.samples`; additional health-query references |
| HomeKit | `home.accessory.set`, `home.scene.run`, `home.security.sweep`, `home.bind_geofence` |
| Calendar / reminders | `calendar.search`, `calendar.events.create/update/delete`, `reminders.*` |
| Contacts | `contacts.search/create/update/delete` |
| Photos | `photo.sync`, `photo.sync_stop`, `media.delete`, `media.favorite`, album operations |
| Messaging | `message.draft`, `message.shortcut_setup`, forwarding App Intents |
| Sync | `data_source.backfill`, `data_source.refresh`, `client.data_source.publish` |

These are compiled names and descriptions, re-read from the node command table (`0x3a3e730`–`0x3a3eec6`) in the 27 September audit. Swift metadata shows a typed approval gate: `HCHNodeHitlMode` is allow / ask / deny, and `HCHNodeHitlRequestKind` is command / dataSourceBackfill / dataSourceRefresh / proactiveSync. The binary logs `Node data sync: node HITL denied proactive sync`. So the gate is real. What it decides is whether a given read or sync runs now; whatever it lets through goes to the VM. It is also weaker than it looks. Flags named `node_hitl_enabled` and `server_hitl_enabled` sit in the same server-controlled config, though what they do to the gate when off was not established. Approvals can also be relayed through the server (`Node HITL server approval opened`, `reason=server_decision`) or given from a notification. The choices include "Always allow" with no stated end. The default mode per data group could not be read statically.

`message.draft` references Apple's message composer, where the user sends the message. This sample does not read the iOS Messages database and has no Android-style notification listener. The full node command table has no camera, microphone, screen-capture or clipboard command; the camera and microphone prompts describe capture the user starts.

## 3. Background sync and remote wakeups

Nine sync-source class names appear in the binary:

```
CalendarSyncSource       ContactsSyncSource       RemindersSyncSource
HealthSyncSource         LocationSyncSource       NotesSyncSource
EmailContextSyncSource   IMessageContextSyncSource HomeKitBridgeSource
```

The 27 September audit re-verified the first eight as Swift classes; `HomeKitBridgeSource` was not re-checked. These sources upload deltas when iOS reports a change and chunked backfills when the agent sends `data_source.backfill`. There are chunked-backfill and incremental-upload strings, and the permitted background-task identifier `com.meta.hatch.nodedata.sync.refreshTask`. The message sources depend on forwarded content; they do not read message history. [Sync evidence](../evidence-ios/06-sync-upload.txt).

The shipped MobileConfig parameter map names server flags for most of this, including `calendar_sync_enabled`, `reminders_sync_enabled`, `nodes_health_background_sync_enabled`, `health_observer_immediate_delivery_enabled`, `health_sync_include_samples`, `camera_roll_sync_enabled`, `apple_notes_enabled`, `node_hitl_enabled` and `server_hitl_enabled`. These names identify configuration areas. Behavior must be established at the flag consumer; schema names alone do not prove that Meta can enable each named path or disable approval enforcement. The verifiers split on the rest. One read the compiled defaults (`node_hitl_enabled` on, `server_hitl_enabled` off). The same verifier found several named sync flags never read by native code, and found `server_hitl_enabled` only chooses whether the approval-card text comes from the server. The other verifier found no defaults in the map. What these flags do to the approval gate when off, and their live server values, were not established. [Findings data, IOS81-03](../evidence-updates/2026-09-27/08-spyware-audit-findings.json).

`HatchVmLockedSilentPushHandler` contains reconnect logic and strings for ignoring pushes when the runtime gate is off, the session is absent or VM identifiers mismatch. A silent push can request background work, but iOS controls delivery and execution; it is not a guarantee that a server can wake the app at any time. Commands dispatched after a wake still pass the approval gate, and are denied (`cannot_prompt`) when a prompt is needed but cannot be shown. [Apple background-push documentation](https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app).

## 4. Photos: one `photo.sync` call turns on ongoing camera-roll sync

The sample contains `HCHHatchMediaSync`, `media_sync.upload_asset`, a local upload manifest and `com.meta.hatch.cameraroll.sync.processingTask`. Strings describe catch-up on Wi-Fi arrival and photo-library changes, conditions-based budgets, permission checks and denial by the node approval gate. [Upload evidence](../evidence-ios/06-sync-upload.txt).

**What `photo.sync` does.** The agent's tool text lets it start a camera-roll upload when it "needs up-to-date photo context or the user asks to share recent photos." The 27 September audit traced the handler. In the reviewed successful handler path, after the Photos permission check, it writes `cameraRollSyncEnabled = true`, the same write the Settings toggle makes. Reaching this write arms automatic sync paths on launch, foreground, Wi-Fi arrival and photo-library changes, subject to the later checks. A periodic BGProcessingTask path is also present, but its execution is not established: the IPA lacks `processing` in `UIBackgroundModes`, which Apple requires for that task class. The observed plist supports a likely scheduling failure, not a measured runtime result. [Apple processing-mode requirement](https://developer.apple.com/documentation/backgroundtasks/bgprocessingtask). The tool text does not mention this; it presents only `full_sync` as persistent. [Findings data, IOS81-01](../evidence-updates/2026-09-27/08-spyware-audit-findings.json).

With `full_sync: true`, the handler also writes `cameraRollSyncBypassLimit = true`. The tool text calls this a persistent override for this and future automatic catch-ups, to be used only after an explicit request to sync all photos. Without it, the tool text describes a per-run cap of roughly 500 on Wi-Fi. That figure is tool-description evidence, not a measured limit.

The Photos permission and a per-run approval check still apply: each automatic run has its own "denied by node HITL gate" path, and automatic sync is skipped for limited Photos access. Both settings appear in Settings as **Camera Roll Sync Enabled** and **Sync Full Camera Roll**. The UI copy says a pause clears on reopening the app; the **Camera Roll Sync** setting is the persistent off-switch. `photo.sync_stop` cancels the current run and does not turn that toggle back off. [Reproduced consent/tool text](../evidence-ios/05-sync-and-consent.txt).

## 5. Health: 110 imported type identifiers, not 110 proven uploads

`nm -u` contains **110 distinct HealthKit type-identifier symbols**, including identifiers for heart rate, blood pressure, glucose, insulin delivery, sleep, nutrition and AFib burden. Separate imported classes include `HKStateOfMind` and `HKWorkoutRoute`. [Reproducible count/list](../evidence-ios/11-health-import-count.txt) · [Broader health excerpts](../evidence-ios/07-health.txt).

Log strings in the binary show `.immediate` background delivery requested for high-velocity types, observation batches committed for upload and chunked health backfill. The code is built to upload raw samples, in the background, for the types the user grants; raw-sample inclusion is also switched by the server flag `health_sync_include_samples`. An import is not a granted permission, a requested read set or proof of transmission; shared health libraries may reference types a feature never uses. The actual set depends on OS support, available records and the per-type Health permissions.

The displayed entitlements contain HealthKit and HealthKit background delivery, and the sample has health-sync/raw-sample-upload strings. The displayed `healthkit.access` array is empty and no clinical-record usage description is present; this review found no declared clinical-record access. [Entitlements](../evidence-ios/03-entitlements.json).

## 6. Location and HomeKit

The sample declares foreground/Always location prompts and a location background mode. `location.set_sharing_mode('always')`, sent by the agent, "starts proactive location updates." The app then monitors significant location changes and sends an update on each change, with skip paths. Monitoring is enforced only after iOS grants Always, and the movement threshold is server-tunable. The tool description says background sharing should be requested only when the user explicitly asks. This is static presence: the code and strings are there, and no location upload was observed. [Location evidence](../evidence-ios/08-location.txt) · [27 September finding](../SPYWARE-VERDICT-2026-09-27.md#ios-81).

`home.accessory.set` and scene commands can request changes to supported accessories. `home.security.sweep` describes reading reachable accessories' states/sensor values. `home.bind_geofence` describes HomeKit actions that "execute automatically" on entering or leaving a location, requiring both HomeKit and Always location permissions. Setup is prompted; no per-run approval step was found in the bridge code, though that was not fully traced. These strings do not show that any particular lock can be opened, or that camera video is available. [Tool text](../evidence-ios/05-agent-tools.txt).

## Retention wording in the app

- On disconnect: *"Previous data shared with {app} won't be removed unless you choose to delete it."*
- iMessage forwarding: *"Messages already shared are not deleted."*
- Deleting chat messages: *"Messages you delete are removed from the conversation but may stay in the agent's memory."*
- Consent footer: *"The info used for your tasks is part of your interactions with {appName}, which we use to improve AI at Meta."*
- Training setting: *"Allow us to use your interactions with Muse to develop and improve AI at Meta."* On iOS the value is loaded from the server and the client default could not be read. The Mac client displays it as on when the server value is missing, and Android's client default is on.
- Support access: *"Allowing access means your chats, memory, and files will be visible to support and your data will no longer be confidential."*
- Protocol: `ssh.operator.updated` carries the status of Meta operator SSH access to your VM, with `/v1/ssh/operator/{enable,disable,status}` routes. [Network evidence](../evidence-ios/16-network-ios.txt).

Details: [CROSS-PLATFORM.md](../reports/CROSS-PLATFORM-BASELINE.md#consent-defaults-and-retention-what-the-apps-say) · [`15-consent-retention-ios.txt`](../evidence-ios/15-consent-retention-ios.txt).

## 7. iMessage, Mail and Notes through user-created Shortcuts

The sample contains `HCHForwardIMessageToHatchAppIntent` and `HCHForwardEmailToHatchAppIntent`. Its guidance asks the user to create a Shortcuts automation that forwards matching new content. It explicitly states **no message-history access**, and describes disabling forwarding or deleting the automation. Previously uploaded messages are not deleted by turning forwarding off. [Sync/Shortcuts evidence](../evidence-ios/06-sync-upload.txt).

Both intents are declared with `openAppWhenRun = false` and `authenticationPolicy = 0`, so they run without opening Muse and are allowed while the phone is locked. The forwarding copy says it sends new messages "and who sent them, including messages other people send you." [Findings data, IOS81-09](../evidence-updates/2026-09-27/08-spyware-audit-findings.json).

The guidance suggests a space in "Message Contains" to match many messages, or selecting senders. A space is **not a universal catch-all**: one-word messages and photos without matching text can be missed. A user-created automation is an authorized OS pathway, not evidence of an iOS sandbox bypass.

Notes copy describes a separately installed export shortcut, labels it a prototype and notes account availability gates. It describes exporting all notes, but strings alone do not establish that the prototype is enabled for retail accounts.

## 8. Shared containers, browser sharing and debug surfaces

- **Shared Meta containers:** `group.com.facebook.hatch`, `group.com.facebook.family`, `group.com.metaplatforms.family` and keychain group `T84QZS65DQ.platformFamily` appear in entitlement metadata for the app and its extensions. These allow sharing with other apps that possess matching entitlements; they do not expose every app's private database, and no specific exchange was traced. [Apple app-group documentation](https://developer.apple.com/documentation/xcode/configuring-app-groups) · [Local metadata](../evidence-ios/03-entitlements.json).
- **Identity/analytics:** `FBFamilyDeviceID`, SKAdNetwork and Meta analytics names are present; no cross-app identity transmission was traced. AdSupport and AppTrackingTransparency are linked, but the Info.plist has no tracking-permission string, so the prompt cannot be shown and the IDFA would read as zeros. [Notable strings/imports](../evidence-ios/10-notable.txt).
- **Share extension:** Safari preprocessing collects URL/title, description, thumbnail/icon URLs and selected text, with description/first-paragraph fallbacks. This is a share-sheet pathway, distinct from the Mac's broad debugger extension. [Extension evidence](../evidence-ios/04-extensions.txt).
- **Three bundled extensions:** Notification Service, Share and Widget. A notification service extension modifies notifications for its own app; it is not an Android-style listener for other apps' notifications. No keyboard or VPN extension appears in this bundle inventory. [Reproduced extension metadata](../evidence-ios/12-extension-metadata.json) · [Apple documentation](https://developer.apple.com/documentation/usernotifications/unnotificationserviceextension).
- **SSH access:** strings include "Meta SSH access," temporary debug-access wording and `https://api.muse.ai/ssh-access/tokens`, and the protocol carries `ssh.operator.updated` for Meta operator SSH into the VM. This review did not establish whether any operator access is active. A `dev` build-branch string does not establish an employee-only rollout. [Evidence](../evidence-ios/10-notable.txt).
- **OHTTP and noVNC:** relay hostnames and remote-VM viewer assets are present. Hostnames alone do not prove which traffic uses a relay. The VNC assets describe viewing a cloud browser, not capturing the phone's screen. [Endpoints](../evidence-ios/09-endpoints.txt).

The 27 September audit looked for and did not find: injected dylibs or unsealed files, agent commands for camera, microphone, screen capture or clipboard, IDFA access, reads of the Messages database, keyboard, VPN, call-directory or credential-provider extensions, and custom root CAs in the bundled trust store. [Verdict §4](../SPYWARE-VERDICT-2026-09-27.md#4-what-was-looked-for-and-not-found).

## Conclusion

**Editorial assessment:** the author calls these broad cloud-agent capabilities “spyware by design.” That judgment does not authenticate the decrypted sample or demonstrate unauthorized collection. Permission denial can block operations. The reported `photo.sync` setting side effect, historical access and third-party data exposure deserve testing, but live defaults, actual uploads, retention and training use remain unverified.

**Limits:** this static audit found no hidden or covert collection channel and did not observe live traffic. The collection is disclosed in consent text, except for the `photo.sync` side effect in §4, and runs through the channels described above. Live server flag values and the default approval mode per data group were not recovered, so which features are on for a given account is not established. Negative string searches for trackers, jailbreak checks or stealth code are limited searches, not proof those behaviours are absent.

## 9. Reduce access or remove it

1. Review Muse connector approvals, turn off ongoing sharing and disable **Camera Roll Sync** rather than only pausing it.
2. Revoke Muse's location, Photos, Contacts, Calendar, Reminders, Home, Bluetooth, camera and microphone permissions in iOS settings as applicable.
3. Revoke Muse's access in the Health app's app-permissions controls.
4. Disable/delete the Shortcuts automations you created for Muse.
5. Disconnect services and remove the app. Use current Muse account/data controls to request cloud deletion; this review has not verified a Muse-specific Accounts Center workflow or backup retention.

## 10. Reproduce the added iOS evidence

On macOS, with Python 3 and Xcode command-line tools:

```bash
unzip com.facebook.hatch_8.1_und3fined.ipa -d /tmp/muse-ipa-review
python3 scripts/collect-review-evidence.py ios com.facebook.hatch_8.1_und3fined.ipa /tmp/muse-ipa-review/Payload/HatchApp.app --output /tmp/muse-ios-review
```

The collector hashes the IPA, records signature display **and verification**, reads plists, lists selected strings and counts imported health identifiers. It never executes app code. It regenerates the machine-readable review files; earlier narrative evidence files remain separately indexed in [EVIDENCE.md](../EVIDENCE.md). The page-hash and CMS checks can now be reproduced with `python3 scripts/verify-september27-audit.py`; see [independent verification](../evidence-updates/2026-09-27/09-independent-verification.json). This verifies metadata and limited byte ranges, not decrypted code authenticity.
