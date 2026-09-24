# Muse for Android (`com.facebook.aura` 8.0.0.21.168)

Static review of the supplied Android APK: **SMS, call logs, notification access, background location and 19 Health Connect data-category permissions**, with an approval-gated background publishing pipeline. These are shipped capabilities, not observed uploads. OS grants, user settings and account configuration still matter.

**Reviewed 2026-09-24.** JADX output includes decompilation warnings, so control-flow conclusions are qualified; the app was never installed or run.

[**iOS**](IOS.md) · [**macOS**](README.md) · [**Android**](ANDROID.md) · [**All evidence**](EVIDENCE.md)

---

## 1. Authenticity

| Field | Value |
|---|---|
| File | `muse-from-meta-8-0-0-21-168.apk` |
| sha256 | `b351a83270b094d2ce565d239180bc226d7426c96d9de7575a47283af926c13d` |
| Package | `com.facebook.aura` (app label "Muse") |
| Version | `8.0.0.21.168` (versionCode `1061301140`), targetSdk 36, minSdk 29 |
| Signer | `CN=Meta Platforms Inc., OU=Meta Mobile, O=Meta Platforms Inc., L=Menlo Park, ST=California, C=US` |
| Cert SHA-256 | `a16bbe0247a738bc8f09fef50d890dc177ec875a83a121f877329b1b89667e99` (RSA 4096, APK Sig Scheme v3) |
| Source Stamp | Verified, signed by Google (`CN=Android, O=Google Inc.`), consistent with Google Play distribution |

APK v3 integrity and the source stamp verify. The displayed certificate identity is Meta; its subject name alone is not an independent trust anchor. This review has not compared the signing key against a separately obtained official-store copy ([`01-signature.txt`](evidence-android/01-signature.txt)).

## 2. Permissions

From the manifest ([`02-permissions.txt`](evidence-android/02-permissions.txt)). A declared permission is a request, not evidence it was granted:

| Category | Permissions |
|---|---|
| **SMS** | `READ_SMS`, `SEND_SMS` |
| **Calls** | `READ_CALL_LOG`, `CALL_PHONE` |
| **Location** | `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, **`ACCESS_BACKGROUND_LOCATION`**, `ACCESS_MEDIA_LOCATION` (GPS inside photos) |
| **Contacts / Calendar** | `READ_CONTACTS`, `WRITE_CONTACTS`, `READ_CALENDAR`, `WRITE_CALENDAR` |
| **Media** | `READ_MEDIA_IMAGES`, `READ_MEDIA_VISUAL_USER_SELECTED`, `CAMERA`, `RECORD_AUDIO`, `FOREGROUND_SERVICE_MICROPHONE` |
| **Health Connect** (19 data types + 2 access, see [`11-health-permission-count.txt`](evidence-android/11-health-permission-count.txt)) | steps, heart rate, **heart-rate variability**, resting HR, **sleep**, exercise, distance, calories (active + total), elevation, floors, **weight, body fat, body water mass, bone mass, lean body mass, height, basal metabolic rate, VO2 max**, plus **`READ_HEALTH_DATA_HISTORY`** and **`READ_HEALTH_DATA_IN_BACKGROUND`** |
| **Persistence** | `RECEIVE_BOOT_COMPLETED`, `FOREGROUND_SERVICE_SPECIAL_USE`, `WAKE_LOCK` |
| **Tracking** | `com.google.android.gms.permission.AD_ID`, install-referrer |
| **Other** | `BLUETOOTH_SCAN/CONNECT`, `ACCESS_WIFI_STATE`, `CHANGE_WIFI_MULTICAST_STATE`, `DETECT_SCREEN_CAPTURE`, `USE_BIOMETRIC`, `SET_ALARM` |

There are **19 health-data category permissions plus two additional-access permissions**, not 21 data types. With user approval and platform support, `READ_HEALTH_DATA_HISTORY` extends access beyond the normal boundary of **30 days before the first permission grant**; that boundary is not a rolling last-30-days window. Background reads also require the separate background permission. [Android Health Connect documentation](https://developer.android.com/health-and-fitness/health-connect/read-data).

`DETECT_SCREEN_CAPTURE` is screenshot-detection permission, not permission to record other apps’ screens. Limited photo selection can constrain gallery access.

## 3. "Execute server-initiated device commands"

Android requires foreground services of type `specialUse` to state their purpose in the manifest. Meta's own wording ([`03-manifest-components.txt`](evidence-android/03-manifest-components.txt)):

> **`NodeCommandService`**: *"Execute server-initiated device commands such as location queries and contact sync"*
>
> **`HatchForegroundService`**: *"Keep the app running in the background at the user's request to continue long-running assistant tasks"*

Commands arrive from Meta's gateway as `client.invoke` frames (`nodes/HatchNodeClient.java`). If Android blocks starting a foreground service, the app falls back to WorkManager (`"FGS start blocked, falling back to WorkManager: command="`). A `HatchBootReceiver` handles `BOOT_COMPLETED` and `MY_PACKAGE_REPLACED` to restore scheduled work. This does not establish uninterrupted execution or bypass Android background/force-stop restrictions.

### Commands the server can invoke

([`04-agent-commands.txt`](evidence-android/04-agent-commands.txt))

```
SMS handlers: MessageSearch / MessageAttachmentGet / MessageDraft / MessageSend
call_log.search        phone.dial
notifications.get      notifications.action (reply, dismiss, press buttons)
location.get           geofence.set / geofence.list / geofence.remove
contacts.search / create / update / delete      calendar.search
photos.search / photos.upload / photos.upload_status
alarm.set / list / update / dismiss / dismiss_all      battery.get
network.state          background.session
```

Many command categories belong to an approval ("human-in-the-loop") group in `nodes/core/NodeHitlGroup.java`: `SMS`, `SMS_SEND`, `CALL_LOG`, `PHONE_CALL`, `NOTIFICATIONS`, `LOCATION`, `HEALTH`, `PHOTOS`, `CONTACTS`, `CALENDAR`, … Where a category mapping exists, saved permissions and the baseline determine whether approval is needed. Mapped **proactive sync** paths use the gate as `NodeHitlRequestKind.PROACTIVE_SYNC` (`nodes/datasource/ProactiveSyncRunner.java`). If no permission default is cached, `HatchNodeHitlGate` **fails closed to `ALWAYS_ASK`** ([`10-review-corrections.txt`](evidence-android/10-review-corrections.txt)). The inspected gate allows persisted allowed modes, denies denied modes, and returns a denial for proactive requests that would otherwise need a prompt. This is evidence of permission checks, not a runtime proof of every path or default.

### Which background paths the gate actually covers

The reviewed background publish paths ([`13-publish-path-gating.txt`](evidence-android/13-publish-path-gating.txt)) show **the gate isn't enforced at the network sink**. Each caller checks it only if `NodeHitlCatalog.forDataSource()` returns a spec, and it does so for **six sources only**: `health`, `contacts`, `calendar`, `call_log`, `sms`, `notifications` (`nodes/core/NodeHitlCatalog.java`). The `LOCATION` approval group exists, but no data source is mapped to it.

| Background path | Trigger | Local category-gate check | Payload fields / capability |
|---|---|---|---|
| Calendar, contacts, call log, SMS sync | content change, app resume | **yes** | records |
| Health sync | Health Connect changes | **yes** (once the gateway is attached) | health samples |
| Notification listener → `publishNow` | posted notifications, subject to access/filtering | **yes** | notification content |
| **Geofence crossing** → `LocationDataSource.publishNow` | entering/leaving a geofence | **no** | **latitude, longitude, timestamp, geofence name** |
| **`network_state`** proactive sync | network change, app attach, boot | **no** | **Wi-Fi SSID, BSSID**, RSSI, link speed, **carrier name**, roaming, VPN on/off |
| `battery` | power broadcasts | **no** | battery state |
| `data_source.backfill` | agent/server command | yes | history |
| Photo upload worker | `photos.upload` command | yes, when queued (retries aren't re-checked) | photos |

Nuances:

- `geofence.set` requests Android foreground/background location grants when missing, but **it also has no `NodeHitlCatalog.forCommand` mapping**. An existing OS grant is not a fresh approval prompt. Crossings can publish coordinates without this local category check; server authorization, source state, deduplication and successful delivery remain separate questions. Boot handling attempts to re-arm geofences.
- A Wi-Fi BSSID identifies a specific router and works as a location fingerprint. The inspected reader sets SSID/BSSID to **null** without fine-location permission or when it receives unknown/scrubbed identifiers. A populated field is not guaranteed.

**How the gate decides for background sync.** It never prompts. It allows silently when the category is set to "allow", or when the category is unset and the cached **server-provided** `connector_default` is `auto_allow`. It denies otherwise, including when nothing is cached. That server default comes from `GET permissions/settings`, and `PermissionDefaultMode.fromWire()` maps a **missing or unrecognized value to `AUTO_ALLOW`**:

```java
return permissionDefaultMode == null ? PermissionDefaultMode.AUTO_ALLOW : permissionDefaultMode;
```

For the six gated categories, a **server-returned, user-editable account setting supplies the fallback when there is no per-category override**. The settings UI also writes this value. An omitted/unrecognized field in a successfully parsed response differs from no cached response: the latter fails closed for unset proactive reads. The client code cannot tell us the production value. It's test D1 in the [research plan](RESEARCH-PLAN.md).

## 4. Proactive sync: data published in the background

The files that publish directly to Meta's `client.data_source.publish` RPC ([`05-proactive-sync-and-backfill.txt`](evidence-android/05-proactive-sync-and-backfill.txt)):

```
commands/health/HealthDataSource.java
commands/location/LocationDataSource.java
commands/notifications/NotificationsDataSource.java
nodes/datasource/ProactiveSyncRunner.java
nodes/datasource/HatchProactiveTriggerManager*.java
startup/gateway/HatchProactiveSyncCatchUpJob.java
```

**Health**, as written in Meta's own code string:

> *"MetaHealthQuery observer polls Health Connect Changes API; HealthSyncManager debounces fires and drives the sync through ProactiveSyncRunner onto the client.data_source.publish sink."*

The code describes polling health-data changes and publishing through the proactive-sync runner. `HealthSyncStartupJob` registers startup work; permissions and the approval gate can prevent collection/publishing.

**Location:**

> *"Current device location (lat, long, accuracy, address), read when the app is open, plus location pushes emitted when a user-registered geofence is crossed."*
> *"geofence broadcast receivers call publishNow() with the crossing coordinates."*

**Calendar:** `CalendarDataSource` sets `emitsProactively = true` and watches the calendar provider (`ProactiveTrigger.ContentObserver`, 5 s debounce), publishing events from 7 days back to 14 days ahead. Backfill runs in 30-day chunks.

**Notifications:** see §5.

**After reboot:** `HatchBootReceiver` enqueues a proactive-sync bootstrap, re-registers geofences, alarms and reminders, and logs `"Forced notification listener rebind via component-enabled toggle"`.

**Backfill** (bulk history import) exists for **SMS, call log, contacts, calendar and health**: `SmsBackfillStrategy`, `CallLogBackfillStrategy`, `ContactsBackfillStrategy`, `HealthBackfillStrategy`. SMS and call log take a `start_date` window (`"start_date is required for sms backfill"`). SMS keeps sync cursors `last_synced_sms_date_ms` and `recently_published_message_ids` and has a `readProactiveMessages` path.

## 5. The notification listener: broad access, with filters and OS limits

`NodeNotificationListenerService` declares `BIND_NOTIFICATION_LISTENER_SERVICE` so the system can bind to it. After the user grants Notification access, it can receive notifications Android exposes to that listener, subject to OS redaction, profiles and app filters ([`06-notification-listener.txt`](evidence-android/06-notification-listener.txt)).

The command description:

> *"Reports the device's current active notifications — app, title, body, sender, and the notification key used by `notifications.action`."*
> `notifications.action`: *"Operate on a device notification by key: reply to a message, dismiss one, dismiss all, or trigger one of its buttons."*

Fields/styles recognized by `NotificationSerializer`; not every notification contains these fields:

```
android.title   android.text   android.bigText   android.textLines
android.messagingStyleUser     android.selfDisplayName   android.picture
MessagingStyle  InboxStyle  BigPictureStyle  CallStyle   app_package   category
```

Notification payloads can contain sender names, message bodies and multi-message summaries. `android.picture` is also inspected. This is not evidence that the full chat history, every image or every message from the originating app is available.

**Default: all apps.** From `gateway/store/HatchGatewayPrefsStore.java`:

```java
return strA01 != null ? PhoneNotificationsAccessMode.valueOf(strA01) : PhoneNotificationsAccessMode.ALL;
} catch (IllegalArgumentException unused) {
    return PhoneNotificationsAccessMode.ALL;
```

`ALL` is the fallback for **which apps are eligible**, not a grant of Android notification access or permission to publish. `BlockedAppsNotificationFilter` does no per-package blocking in that mode; `SELECTED` uses the stored blocked-app list. `HatchNotificationFilterManager` also installs `WorkAppNotificationFilter`. Both filters must be considered. [Evidence](evidence-android/10-review-corrections.txt).

**OTP filtering is unresolved at the app/server level.** The original keyword search found no `otp`, `one-time`, `verification code`, `2fa` or `two-factor` matches in two directories. That cannot prove the app has no filtering in shared/obfuscated code or on its backend. **Android 15+ redacts detected OTP notification content from untrusted notification listeners**, with exceptions for trusted apps. The sample targets SDK 36 but supports older Android versions; neither target SDK nor the permission list establishes its runtime trust status. This OS protection concerns notification delivery, not all SMS database reads. [Android 15 behavior changes](https://developer.android.com/about/versions/15/behavior-changes-all).

`NotificationsDataSource` has a sync cursor and publishes through `client.data_source.publish`. **Its `publishNow` path checks both managed configuration and `HatchNodeHitlGate` with `PROACTIVE_SYNC`.** The previous claim that MDM was its only off-switch was incorrect. Revoking Android Notification access is another control. [Code excerpts](evidence-android/10-review-corrections.txt).

### Training, deletion and support access (app text)

- The client AI-training fallback is on: `HatchAiTrainingApi.DEFAULT_ENABLED = true`; the response-model fallback is also true. Fresh-account server state remains untested.
- Generic connector footer: *"Info from this connector is part of your AI interactions, which we use to improve AI at Meta."* Health Connect has a distinct variant saying **“may use”** (resource `0x7f1206e7`). This is disclosure language, not a trace of raw records entering training.
- Deleting a message: *"Messages you delete are removed from the conversation but may stay in the agent's memory."*
- Support access: *"Allowing access means your chats, memory, and files will be visible to support and your data will no longer be confidential."*
- The consent sheets for SMS, notifications, health and location describe sharing **after** you connect. The code still declares `supportsBackfill = true` for SMS, call log and health.

Details: [CROSS-PLATFORM.md](CROSS-PLATFORM.md#consent-defaults-and-retention-what-the-apps-say) · [`15-consent-retention-android.txt`](evidence-android/15-consent-retention-android.txt).

## 6. Photos

`commands/photos` ([`08-photos.txt`](evidence-android/08-photos.txt)) contains:

- `MlKitPhotoLabeler`, `PhotoLabelScanner`, `PhotoLabelDatabase`: **on-device ML Kit labeling** of your gallery, cached in a local database so the agent can search photos by content.
- `PhotoUploadWorker`, `PhotoUploadDatabase`, `MediaDeviceSyncClient`: a background upload queue (`"Draining … queued photos"`, `"Uploaded photo "`) sending `original_filename`, `platform_asset_id` and the image.
- `photos.upload` accepts up to 50 photo IDs per call (`"photo_ids accepts at most 50 photos per call"`).
- `ACCESS_MEDIA_LOCATION` requests access to location metadata in accessible photos; it does not prove every photo has GPS data or that access was granted.

The inspected `photos.upload` interface is batch-oriented, with on-device labeling and a background upload queue. This does not establish a whole-library mirror, prove no other upload route exists, or mean photos outside the user’s granted access are scanned.

## 7. Other notable pieces

([`09-notable.txt`](evidence-android/09-notable.txt))

- **On-device MCP server + agentic runtime**: `libmcp_server_jni.so`, `libagentic_runtime_jni.so`, `libxplat_agentic_client_AgenticRemoteClientAndroid.so`, `libxplat_mcp-sdk_…__2025-06-18__mobileAndroid.so`. These libraries indicate bundled MCP/runtime support; library names alone do not establish which protocols every network connection uses.
- **`assets/vmvnc/`** (noVNC `vnc.html` + `novnc-rfb.js`): a VNC viewer for watching the **cloud VM's desktop** from the phone.
- **`FoaPhoneIdProvider` + `FoaPhoneIdRequestReceiver`**: both exported with no manifest permission, and both answer with Meta's "Family of Apps" device ID (a random UUID shared across Meta apps on the phone; the oldest wins), its origin and timestamp. **They are caller-checked in code:** the provider compares the calling app's signing-certificate SHA-256 against an allow-list of 11 hashes (including Muse's own) plus two pinned research apps, `com.facebook.study` and `com.facebook.viewpoints`. Anyone else gets `"Caller Identity … is not trusted"`. The receiver requires an "auth" `PendingIntent` whose creator passes the same check. **Untrusted callers are rejected by the inspected checks**; this supports intended Family-of-Apps sharing, not an unconditional proof against every bypass. Other allow-listed certificates were not individually attributed, and the trusted-caller decompilation has unresolved branches ([`12-phone-id-provider.txt`](evidence-android/12-phone-id-provider.txt)).
- **`HatchVoiceInteractionService`**: can register as the phone's **default digital assistant** (long-press home / "assist" gesture).
- **`HatchXInstallReferrerReceiver`** + `AD_ID` + Facebook `analytics2` uploaders: standard Meta attribution and analytics.
- **Oxygen preloads SDK** (`com.facebook.oxygen.preloads…`): Meta's first-party SDK tied to its preloaded-app infrastructure.

## 8. Summary

| Shipped capability / observation | Static evidence |
|---|---|
| Read & send SMS, bulk SMS backfill | `READ_SMS`/`SEND_SMS`, `SmsDataSource`, `SmsBackfillStrategy` |
| Read call history, backfill | `READ_CALL_LOG`, `CallLogDataSource`, `CallLogBackfillStrategy` |
| Place phone calls | `CALL_PHONE`, `phone.dial` |
| Read exposed notifications and invoke available notification actions, subject to grants/filters | `NodeNotificationListenerService`, `NotificationSerializer`, `notifications.action`, default `ALL` |
| No app-level OTP conclusion; Android 15+ redaction applies to untrusted listeners | bounded keyword search plus Android platform documentation |
| Background location + geofence pushes, **no local category-gate check on crossings** | `ACCESS_BACKGROUND_LOCATION`, `LocationDataSource.publishNow`, `NodeHitlCatalog` (6 gated sources) |
| Wi-Fi SSID/BSSID + carrier published in background, **no local category-gate check** | `commands/network/NetworkStateHandlerKt.java`, `AuraProactiveSyncWorker` |
| Server-returned baseline for unset categories: omitted/unrecognized field → `AUTO_ALLOW`; no cache → proactive deny | `PermissionDefaultMode.fromWire` |
| 19 health-data category permissions, extended history/background access requested, proactive publishing code | Health Connect perms, `HealthSyncManager` → `client.data_source.publish` |
| Server-initiated commands | manifest: *"Execute server-initiated device commands…"* |
| Re-registers work after boot/update, subject to OS restrictions | `HatchBootReceiver` |
| Cross-app identity sharing with certificate allow-list checks | exported `FoaPhoneIdProvider` (`com.facebook.GET_PHONE_ID`) |

## 9. Remove it

1. Settings → Apps → Special app access → **Notification access** → turn Muse **off**.
2. Settings → Apps → Muse → Permissions → deny **SMS, Call logs, Phone, Location, Contacts, Calendar, Photos, Camera, Microphone, Nearby devices**.
3. Health Connect → App permissions → Muse → **Remove all** and delete Muse's data access.
4. Settings → Apps → Default apps → **Digital assistant app**: switch away from Muse if it was set.
5. Disconnect connectors and uninstall. Use Muse’s current account/data controls to request removal of previously uploaded data; this review has not verified a Muse-specific Accounts Center deletion workflow. Uninstalling does not demonstrate cloud deletion.

## 10. Reproduce the Android checks

Use Android SDK Build Tools (`apksigner`, `aapt2`) and JADX; none of these commands installs or launches the APK:

```bash
apksigner verify --print-certs -v muse-from-meta-8-0-0-21-168.apk
aapt2 dump badging muse-from-meta-8-0-0-21-168.apk
aapt2 dump permissions muse-from-meta-8-0-0-21-168.apk
aapt2 dump xmltree muse-from-meta-8-0-0-21-168.apk --file AndroidManifest.xml
jadx -d /tmp/muse-jadx muse-from-meta-8-0-0-21-168.apk
python3 scripts/collect-review-evidence.py android /tmp/muse-jadx/sources evidence-android --output /tmp/muse-android-review
```

JADX can report errors and still write partial output. Record its version and warnings, and do not treat decompiled coroutine control flow as equivalent to verified source. The collector rebuilds the new review excerpts/count; it does not recreate all earlier evidence files. Compare fresh manifest output with the committed permission list before relying on its derived count.

---

*Static analysis only (apksigner, aapt2, jadx 1.x decompile). The app was never installed or run. Decompiled Meta code is not included in this repo; only short excerpts and grep output.*
