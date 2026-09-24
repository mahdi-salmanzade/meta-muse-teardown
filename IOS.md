# Muse for iOS (`com.facebook.hatch` 8.1.0)

**The supplied iOS sample contains HealthKit, HomeKit, background-location and photo-sync functionality, plus Shortcuts-based message forwarding.** These findings describe an unverified, decrypted-looking IPA. They are not proof that every feature is enabled or that any data was uploaded.

[**iOS**](IOS.md) · [**macOS**](README.md) · [**Android**](ANDROID.md) · [**All evidence**](EVIDENCE.md)

Reviewed **2026-09-24**. Nothing was installed or launched.

## 1. Provenance: consistent with a decrypted App Store package, not fully authenticated

| Field | Observed value |
|---|---|
| File | `com.facebook.hatch_8.1_und3fined.ipa` |
| SHA-256 | `70c3cfe5bde49e31eecd087fdbb6749703d2dd74f124c7c464866884d72603b2` |
| Bundle / version | `com.facebook.hatch`, 8.1.0, build `1074192126` |
| Internal version / build date | `8.1.0.8.136` / `2026-09-22T07:00:13` |
| Minimum OS | iOS 18.0 |
| Displayed signature metadata | Apple iPhone OS Application Signing chain; TeamIdentifier `V9WTTPBFK9` |
| Actual signature verification | **Fails:** `invalid signature (code or signature have been modified)` |
| Main executable encryption command | `cryptid 0`, `cryptoff 16384`, `cryptsize 72089600` |

[Reproducible signature/encryption output](evidence-ios/01-provenance.txt) · [Selected Info.plist](evidence-ios/02-info-plist.json).

The earlier [page-hash inspection](evidence-ios/01-authenticity.txt) reports mismatches confined to the encrypted regions and the changed `cryptid` field, with matching remaining pages/resources. That is **consistent with decryption**, but cannot rule out edits within the decrypted regions. Displaying a signing certificate does not validate the changed executable. This report therefore does not call the sample an unmodified, authenticated Meta binary.

The [US App Store listing](https://apps.apple.com/us/app/muse-from-meta/id6760173601) independently lists Meta as the seller and version 8.1 as of the review date. Matching marketing versions do not establish byte-for-byte identity. The original IPA acquisition chain was not recorded here.

## 2. Agent commands and approval evidence

[Tool excerpts](evidence-ios/05-agent-tools.txt) and [reproduced command/event names](evidence-ios/04-command-names.txt) show:

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

These are compiled names/descriptions, not a runtime-confirmed registration list. The binary contains approval prompts, persistent-allow UI copy and `Node data sync: node HITL denied proactive sync`. That contradicts an assumption that all background publishing bypasses permission checks. Enforcement and production defaults remain untested.

`message.draft` references Apple’s message composer, where the user sends the message. This sample does not establish direct reading of the iOS Messages database or an Android-style notification listener. The camera usage prompt is present; absence of a `camera.*` agent command would not establish absence of camera functionality.

## 3. Background sync and remote wakeups

Nine sync-source class names appear in the binary:

```
CalendarSyncSource       ContactsSyncSource       RemindersSyncSource
HealthSyncSource         LocationSyncSource       NotesSyncSource
EmailContextSyncSource   IMessageContextSyncSource HomeKitBridgeSource
```

There are chunked-backfill and incremental-upload strings, as well as the permitted background-task identifier `com.meta.hatch.nodedata.sync.refreshTask`. The existence of a sync-source class does not mean it can independently read all historical data; the message sources depend on forwarded content. [Sync evidence](evidence-ios/06-sync-upload.txt).

`HatchVmLockedSilentPushHandler` contains reconnect logic and strings for ignoring pushes when the runtime gate is off, the session is absent or VM identifiers mismatch. A silent push can request background work, but iOS controls delivery and execution; it is not a guarantee that a server can wake the app at any time. [Apple background-push documentation](https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app).

## 4. Photos: ongoing upload, full-library override and a temporary pause

The sample contains `HCHHatchMediaSync`, `media_sync.upload_asset`, a local upload manifest and `com.meta.hatch.cameraroll.sync.processingTask`. Strings describe catch-up on Wi-Fi arrival and photo-library changes, conditions-based budgets, permission checks and denial by the node approval gate. [Upload evidence](evidence-ios/06-sync-upload.txt).

**A distinction that matters:** the tool text describes `full_sync: true` as a persistent override for this and future automatic catch-ups, to be used only after an explicit request to sync all photos. It describes a normal per-run cap of roughly 500 on Wi-Fi. That figure is tool-description evidence, not a measured limit.

The UI copy says a pause clears on reopening the app; the **Camera Roll Sync** setting is the persistent off-switch. `photo.sync_stop` cancels the current run without disabling future automatic sync. Other strings say automatic sync is skipped for limited Photos access. These controls are omitted by simply calling the feature a whole-library mirror. [Reproduced consent/tool text](evidence-ios/05-sync-and-consent.txt).

## 5. Health: 110 imported type identifiers, not 110 proven uploads

`nm -u` contains **110 distinct HealthKit type-identifier symbols**, including identifiers for heart rate, blood pressure, glucose, insulin delivery, sleep, nutrition and AFib burden. Separate imported classes include `HKStateOfMind` and `HKWorkoutRoute`. [Reproducible count/list](evidence-ios/11-health-import-count.txt) · [Broader health excerpts](evidence-ios/07-health.txt).

**An import is not a granted permission, a requested read set or proof of transmission.** Shared health libraries may reference types unused by a particular feature. Actual access depends on OS support, available records and the user’s per-type Health permissions.

The displayed entitlements contain HealthKit and HealthKit background delivery, and the sample has health-sync/raw-sample-upload strings. The displayed `healthkit.access` array is empty and no clinical-record usage description is present; this review found no declared clinical-record access. [Entitlements](evidence-ios/03-entitlements.json).

## 6. Location and HomeKit

The sample declares foreground/Always location prompts and a location background mode. Strings describe significant-location-change monitoring and upload events, with skip paths. The tool description says background sharing should be requested only when the user explicitly asks, and requires OS authorization. [Location evidence](evidence-ios/08-location.txt).

`home.accessory.set` and scene commands can request changes to supported accessories. `home.security.sweep` describes reading reachable accessories’ states/sensor values. `home.bind_geofence` describes automatic HomeKit actions on entering or leaving a location, requiring both HomeKit and Always location permissions. These are consequential capabilities; they do not prove that any particular lock can be opened, or that camera video is available. [Tool text](evidence-ios/05-agent-tools.txt).

## Retention wording in the app

- On disconnect: *"Previous data shared with {app} won't be removed unless you choose to delete it."*
- iMessage forwarding: *"Messages already shared are not deleted."*
- Consent footer: *"The info used for your tasks is part of your interactions with {appName}, which we use to improve AI at Meta."*

Details: [CROSS-PLATFORM.md](CROSS-PLATFORM.md#consent-defaults-and-retention-what-the-apps-say) · [`15-consent-retention-ios.txt`](evidence-ios/15-consent-retention-ios.txt).

## 7. iMessage, Mail and Notes through user-created Shortcuts

The sample contains `HCHForwardIMessageToHatchAppIntent` and `HCHForwardEmailToHatchAppIntent`. Its guidance asks the user to create a Shortcuts automation that forwards matching new content. It explicitly states **no message-history access**, and describes disabling forwarding or deleting the automation. Previously uploaded messages are not deleted merely by turning forwarding off. [Sync/Shortcuts evidence](evidence-ios/06-sync-upload.txt).

The guidance suggests a space in “Message Contains” to match many messages, or selecting senders. A space is **not a universal catch-all**: one-word messages and photos without matching text can be missed. A user-created automation is an authorized OS pathway, not evidence of an iOS sandbox bypass.

Notes copy describes a separately installed export shortcut, labels it a prototype and notes account availability gates. It describes exporting all notes, but strings alone do not establish that the prototype is enabled for retail accounts.

## 8. Shared containers, browser sharing and debug surfaces

- **Shared Meta containers:** `group.com.facebook.family`, `group.com.metaplatforms.family` and `T84QZS65DQ.platformFamily` appear in entitlement metadata. These allow sharing with other apps that possess matching entitlements; they do not expose every app’s private database or prove a particular exchange occurred. [Apple app-group documentation](https://developer.apple.com/documentation/xcode/configuring-app-groups) · [Local metadata](evidence-ios/03-entitlements.json).
- **Identity/analytics:** `FBFamilyDeviceID`, IDFA-related imports, SKAdNetwork and Meta analytics names are present. This is not proof of actual cross-app identity transmission or successful IDFA access. [Notable strings/imports](evidence-ios/10-notable.txt).
- **Share extension:** Safari preprocessing collects URL/title, description, thumbnail/icon URLs and selected text, with description/first-paragraph fallbacks. This is a share-sheet pathway, distinct from the Mac’s broad debugger extension. [Extension evidence](evidence-ios/04-extensions.txt).
- **Three bundled extensions:** Notification Service, Share and Widget. A notification service extension modifies notifications for its own app; it is not an Android-style listener for other apps’ notifications. No keyboard or VPN extension appears in this bundle inventory. [Reproduced extension metadata](evidence-ios/12-extension-metadata.json) · [Apple documentation](https://developer.apple.com/documentation/usernotifications/unnotificationserviceextension).
- **Temporary SSH-access UI:** strings include “Meta SSH access,” temporary debug-access wording and `https://api.muse.ai/ssh-access/tokens`. These identify a debug-access surface, not proof that Meta staff have active access or that the UI is publicly enabled. A `dev` build-branch string does not establish an employee-only rollout. [Evidence](evidence-ios/10-notable.txt).
- **OHTTP and noVNC:** relay hostnames and remote-VM viewer assets are present. Hostnames alone do not prove which traffic uses a relay. The VNC assets describe viewing a cloud browser, not capturing the phone’s screen. [Endpoints](evidence-ios/09-endpoints.txt).

Negative string searches for trackers, jailbreak checks or stealth code are limited searches, not proof those behaviors are absent. The earlier “clean in this build” conclusion was too broad.

## 9. Reduce access or remove it

1. Review Muse connector approvals, turn off ongoing sharing and disable **Camera Roll Sync** rather than only pausing it.
2. Revoke Muse’s location, Photos, Contacts, Calendar, Reminders, Home, Bluetooth, camera and microphone permissions in iOS settings as applicable.
3. Revoke Muse’s access in the Health app’s app-permissions controls.
4. Disable/delete the Shortcuts automations you created for Muse.
5. Disconnect services and remove the app. Use current Muse account/data controls to request cloud deletion; this review has not verified a Muse-specific Accounts Center workflow or backup retention.

## 10. Reproduce the added iOS evidence

On macOS, with Python 3 and Xcode command-line tools:

```bash
unzip com.facebook.hatch_8.1_und3fined.ipa -d /tmp/muse-ipa-review
python3 scripts/collect-review-evidence.py ios com.facebook.hatch_8.1_und3fined.ipa /tmp/muse-ipa-review/Payload/HatchApp.app --output /tmp/muse-ios-review
```

The collector hashes the IPA, records signature display **and verification**, reads plists, lists selected strings and counts imported health identifiers. It never executes app code. It regenerates the machine-readable review files; earlier narrative evidence files remain separately indexed in [EVIDENCE.md](EVIDENCE.md). The earlier page-hash analysis is not reproduced by this collector.
