# Muse for Android (`com.facebook.aura` 8.0.0.21.168)

**The reviewed Android client can send permitted command results and sync records to a Meta-hosted VM. Permission denial can stop access; approval alone does not prove a successful upload.** This report describes client capabilities and gates, not traffic captured from a live account.

The Android app is built to read and upload:

- **SMS and call logs**, with ongoing sync after you connect.
- **Notifications from all apps by default**, once Notification access is granted: app, title, body and sender.
- **19 Health Connect data categories**, plus the extra permissions for older history and background reads.
- **Background location**, with geofence crossings that publish coordinates.
- **Contacts and calendar**, with ongoing sync.
- **History backfill** for SMS, call log, contacts, calendar and health. In the 9.0 audit the reviewed paths have **no app-level connection-date clamp identified**, while the Messages, Call Log and Health consent sheets say "shared after you connect".

Once the data is there, the app's own text says previous data shared "won't be removed unless you choose to delete it" when you disconnect, deleted messages "may stay in the agent's memory", connector info is part of interactions Meta "may use to improve AI", and granting support access means "your data will no longer be confidential". The client training switch falls back to on. The gates are weaker than they look: a server-supplied account baseline decides whether reads run without a prompt, location and network-state paths have no Muse approval step, and the per-source storage value defaults on and its setter has no statically resolved caller; per-category approval modes and OS grants still apply (9.0 audit). Consent is also one person's. SMS threads, call logs, contacts and notifications describe other people whose consent this audit did not establish.

**Editorial assessment:** the author calls this “spyware by design”; this is not a demonstrated finding of covert collection or inevitable upload. The conclusion and the audit's limits are in [§8](#8-summary).

**Reviewed 2026-09-24** against the 8.0 APK. JADX output includes decompilation warnings, so control-flow conclusions are qualified; the app was never installed or run. **27 September:** the [9.0.0.11.178 follow-up](RELEASE-AUDIT-2026-09-27.md#3-what-changed-on-android) and the [spyware audit](SPYWARE-VERDICT-2026-09-27.md) checked the newer APK at the byte and DEX-instruction level. Where they correct or extend this file, the text is marked **9.0 audit**. Those notes come from 9.0; the rest of this file documents 8.0.

[**iOS**](IOS.md) · [**macOS**](README.md) · [**Android**](ANDROID.md) · [**All evidence**](EVIDENCE.md) · [**Spyware verdict**](SPYWARE-VERDICT-2026-09-27.md)

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

**9.0 audit:** every byte of the 9.0 APK is accounted for, both embedded-certificate code-transparency signatures verify (41 and 44 ordinary file hashes match; the custom manifest digest was not independently verified), the signing certificate matches this 8.0 sample, and no dynamic code loading or downloaded modules were identified by the recorded searches; this is a bounded negative result ([spyware audit §1](SPYWARE-VERDICT-2026-09-27.md#1-integrity-every-byte-accounted-for)).

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

**9.0 audit:** an unset category resolves by access type. Unset **reads** resolve to allow; unset **writes** resolve to ask. The server baseline can only turn an allowed read into ask, never relax a write. So sending SMS, placing calls, acting on notifications and editing contacts or calendar prompt unless the user chose "allow". Reading SMS, call logs, contacts, calendar, notifications and (once the server flag is on) photos does not prompt when the category is unset and the baseline is `auto_allow`.

### Which background paths the gate actually covers

The reviewed background publish paths ([`13-publish-path-gating.txt`](evidence-android/13-publish-path-gating.txt)) show **the gate isn't enforced at the network sink**. Each caller checks it only if `NodeHitlCatalog.forDataSource()` returns a spec, and it does so for **six sources only**: `health`, `contacts`, `calendar`, `call_log`, `sms`, `notifications` (`nodes/core/NodeHitlCatalog.java`). The `LOCATION` approval group exists, but no data source is mapped to it.

| Background path | Trigger | Local category-gate check | Payload fields / capability |
|---|---|---|---|
| Calendar, contacts, call log, SMS sync | content change, app resume | **yes** | records |
| Health sync | Health Connect changes | **yes** (once the gateway is attached) | health samples |
| Notification listener → `publishNow` | posted notifications, subject to access/filtering | **yes** | notification content |
| **Geofence crossing** → `LocationDataSource.publishNow` | entering/leaving a geofence | **no** | **latitude, longitude, timestamp, geofence name** |
| **`location.get`** command (9.0 audit) | agent/server command | **no** (Android location permission only) | current location |
| **`network_state`** proactive sync | 8.0: network change, app attach, boot. 9.0: app open, gateway connected | **no** | **Wi-Fi SSID, BSSID**, RSSI, link speed, **carrier name**, roaming, VPN on/off |
| `battery` | 8.0: power broadcasts. 9.0: app open | **no** | battery state |
| `data_source.backfill` | agent/server command | yes; silent when the category is unset and the baseline is `auto_allow` | history, **no app-level connection-date clamp identified** (9.0 audit) |
| Photo upload worker | `photos.upload` command | yes, when queued (retries aren't re-checked) | photos |

**9.0 audit corrections to this table:**

- **`location.get` is also unmapped**, not only geofences. `NodeHitlCatalog.forCommand` returns null for `location.get` and for `geofence.set`, `geofence.list` and `geofence.remove`. Remote location reads run with only the Android location grant, and a backgrounded read depends only on the background-location grant that `geofence.set` requests. The in-app "Share location" setting (Never / When using the app / Always) only mirrors the Android permission. Geofence crossings do post a local "Location reminders" notification.
- **`network_state` and `battery` fire on app open in 9.0** (`ProactiveTrigger.AppOpen`, `TRANSIENT` delivery), not on boot or in the background. They run on every foreground resume of a signed-in session once the gateway connects. The old 8.0 connectivity-change worker returns early for `network_state`. The commands `network.state` and `battery.get` are also unmapped. No compiled user-facing string describes Wi-Fi name, BSSID, carrier or network reporting (server-delivered UI and the privacy policy were not checked). SSID and BSSID are filled only when fine location is granted.
- **Photos** are covered in [§6](#6-photos).

Nuances:

- `geofence.set` requests Android foreground/background location grants when missing, but **it also has no `NodeHitlCatalog.forCommand` mapping**. An existing OS grant is not a fresh approval prompt. Crossings can publish coordinates without this local category check; server authorization, source state, deduplication and successful delivery remain separate questions. Boot handling attempts to re-arm geofences.
- A Wi-Fi BSSID identifies a specific router and works as a location fingerprint. The inspected reader sets SSID/BSSID to **null** without fine-location permission or when it receives unknown/scrubbed identifiers. A populated field is not guaranteed.

**How the gate decides for background sync.** It never prompts. It allows silently when the category is set to "allow", or when the category is unset and the cached **server-provided** `connector_default` is `auto_allow`. It denies otherwise, including when nothing is cached. That server default comes from `GET permissions/settings`, and `PermissionDefaultMode.fromWire()` maps a **missing or unrecognized value to `AUTO_ALLOW`**:

```java
return permissionDefaultMode == null ? PermissionDefaultMode.AUTO_ALLOW : permissionDefaultMode;
```

For the six gated categories, a **server-returned, user-editable account setting supplies the fallback when there is no per-category override**. The settings UI also writes this value. An omitted/unrecognized field in a successfully parsed response differs from no cached response: the latter fails closed for unset proactive reads. The client code cannot tell us the production value. It's test D1 in the [research plan](RESEARCH-PLAN.md).

**9.0 audit:** the setting is labelled "Connector defaults" in Settings → Permissions, and only that screen writes it. Onboarding never asks about it, so a new account starts with whatever value the server sends. The bundled label for `auto_allow` reads "Ask for some actions: Before every write and some read actions". For mapped reads with no saved category override, `auto_allow` can omit a per-action prompt; explicit ask/deny choices still apply. This does not establish the effective mode for every device read. The server can also replace that copy. The per-source switch `slv_data_source_<id>` defaults to on, and the reviewed setter, `HatchDataSourceRegistry.setUserEnabled`, has no statically resolved caller. No UI route to that setter was established; this does not exclude reflection, other storage writers or OS revocation. The remaining in-app control is the per-category approval mode on the connector-permissions screen, which only the user (or an "allow always" answer) can set.

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

The code describes polling health-data changes and publishing through the proactive-sync runner. `HealthSyncStartupJob` registers startup work; permissions and the approval gate can prevent collection/publishing. **9.0 audit:** the health connector also sits behind the server flag `hatch_android.health_connect_connector_enabled`. The finder read its compiled default as off; a verifier could not confirm that from the bytes, because the flag read passes no explicit default. Before the gateway attaches, publish frames are dropped, so nothing is sent early.

**Location:**

> *"Current device location (lat, long, accuracy, address), read when the app is open, plus location pushes emitted when a user-registered geofence is crossed."*
> *"geofence broadcast receivers call publishNow() with the crossing coordinates."*

**Calendar:** `CalendarDataSource` sets `emitsProactively = true` and watches the calendar provider (`ProactiveTrigger.ContentObserver`, 5 s debounce), publishing events from 7 days back to 14 days ahead. Backfill runs in 30-day chunks.

**Notifications:** see §5.

**After reboot:** `HatchBootReceiver` enqueues a proactive-sync bootstrap, re-registers geofences, alarms and reminders, and logs `"Forced notification listener rebind via component-enabled toggle"`. **9.0 audit:** the listener rebind runs only after an app update, not after a reboot, and geofences are re-armed only while both location grants remain.

**Backfill** (bulk history import) exists for **SMS, call log, contacts, calendar and health**: `SmsBackfillStrategy`, `CallLogBackfillStrategy`, `ContactsBackfillStrategy`, `HealthBackfillStrategy`. SMS and call log take a `start_date` window (`"start_date is required for sms backfill"`). SMS keeps sync cursors `last_synced_sms_date_ms` and `recently_published_message_ids` and has a `readProactiveMessages` path.

**9.0 audit: the reviewed backfill paths do not clamp dates to connection time.** The server sends `data_source.backfill` over the gateway. The client requires a `start_date` but accepts any ISO-8601 date for SMS, call log, contacts, calendar and health. SMS and Call Log pass their date windows to chunked `DataSourcePublishPipeline.deliver` publishing; Health has its own backfill handler. Nothing clamps the window to the connect date or to the SMS sync cursor. The consent copy is potentially ambiguous for three of the five sources. Calendar and Contacts say the agent will "store existing information". Messages, Call Log and Health say "shared after you connect". The gate runs as `DATA_SOURCE_BACKFILL`. If it asks, the prompt shows the start date. It runs silently when the category is unset and the baseline is `auto_allow`, or after "allow always". Whether Meta's server ever requests a window from before the connect date cannot be seen in the client. “Shared after you connect” may describe sharing time rather than record age. Health Connect also imposes OS history limits unless the required extended-history permission is granted; accepting a date does not bypass those limits.

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

Notification payloads can contain sender names, message bodies and multi-message summaries. This is not evidence that the full chat history, every image or every message from the originating app is available. **9.0 audit:** `android.picture` is only a presence check. The serialized keys are `key`, `app_package`, `title`, `category`, `body`, `sender`, `dedup_key` and `timestamp`. No image bytes are compressed, encoded or sent.

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

What the app says happens to the data once it is on Meta's side:

- The client AI-training fallback is on: `HatchAiTrainingApi.DEFAULT_ENABLED = true`, the local starting value of a setting the server refreshes. The response-model fallback is also true. Fresh-account server state remains untested. The opt-out text is forward-looking: interactions "won't be used to improve AI at Meta **after** you turn this off".
- Custom and cloud connector footer: *"Info from this connector is part of your AI interactions, which we use to improve AI at Meta."* Every on-device connector footer, including SMS, call log, notifications, location and Health Connect (resource `0x7f1206e7`), says the info is part of your interactions with Muse, *"which we **may use** to improve AI at Meta."* This audit did not trace records into training.
- Disconnecting: *"You can ask your agent to delete this info at any time, or disconnect from Calendar in your device's settings to prevent future syncing."* Disconnecting stops future syncing. The disconnect sheet for connected apps (`0x7f1206c4`) adds: *"Previous data shared with %1$s won't be removed unless you choose to delete it."*
- Deleting a message: *"Messages you delete are removed from the conversation but may stay in the agent's memory."*
- Support access: *"Allowing access means your chats, memory, and files will be visible to support and your data will no longer be confidential."*
- Operator access: the gateway protocol carries `ssh.operator.updated`, the status of **Meta operator SSH access** to your VM (`v1/ssh/operator/enable`, `/disable`) ([`16-network-android.txt`](evidence-android/16-network-android.txt)).
- The consent sheets for SMS, call log, notifications, health and location describe sharing **after** you connect. The code still declares `supportsBackfill = true` for SMS, call log and health, and the reviewed 9.0 paths do not clamp dates to connection time ([§4](#4-proactive-sync-data-published-in-the-background)).

Details: [CROSS-PLATFORM.md](CROSS-PLATFORM.md#consent-defaults-and-retention-what-the-apps-say) · [`15-consent-retention-android.txt`](evidence-android/15-consent-retention-android.txt).

## 6. Photos

`commands/photos` ([`08-photos.txt`](evidence-android/08-photos.txt)) contains:

- `MlKitPhotoLabeler`, `PhotoLabelScanner`, `PhotoLabelDatabase`: **on-device ML Kit labeling** of your gallery, cached in a local database so the agent can search photos by content.
- `PhotoUploadWorker`, `PhotoUploadDatabase`, `MediaDeviceSyncClient`: a background upload queue (`"Draining … queued photos"`, `"Uploaded photo "`) sending `original_filename`, `platform_asset_id` and the image.
- `photos.upload` accepts up to 50 photo IDs per call (`"photo_ids accepts at most 50 photos per call"`).
- `ACCESS_MEDIA_LOCATION` requests access to location metadata in accessible photos; it does not prove every photo has GPS data or that access was granted.

The inspected `photos.upload` interface is batch-oriented, with on-device labeling and a background upload queue. This does not establish a whole-library mirror, prove no other upload route exists, or mean photos outside the user’s granted access are scanned.

**9.0 audit:** the photo commands are switched by the server flag `hatch_media_sync.is_nodes_media_enabled`, whose compiled default is off. When Meta turns it on, `photos.upload` is classed as a photo **read**, so under an `auto_allow` baseline an upload of up to 50 photos runs with no prompt. "Look up photos" and "Copy photos to your library" share one saved permission (`photos_read`), so allowing search also allows upload. When a prompt does appear, its copy names the upload.

## 7. Other notable pieces

([`09-notable.txt`](evidence-android/09-notable.txt))

- **On-device MCP server + agentic runtime**: `libmcp_server_jni.so`, `libagentic_runtime_jni.so`, `libxplat_agentic_client_AgenticRemoteClientAndroid.so`, `libxplat_mcp-sdk_…__2025-06-18__mobileAndroid.so`. These libraries indicate bundled MCP/runtime support; library names alone do not establish which protocols every network connection uses.
- **`assets/vmvnc/`** (noVNC `vnc.html` + `novnc-rfb.js`): a VNC viewer for watching the **cloud VM's desktop** from the phone.
- **`FoaPhoneIdProvider` + `FoaPhoneIdRequestReceiver`**: both exported with no manifest permission, and both answer with Meta's "Family of Apps" device ID (a random UUID shared across Meta apps on the phone; the oldest wins), its origin and timestamp. **They are caller-checked in code:** the provider compares the calling app's signing-certificate SHA-256 against an allow-list of 11 hashes (including Muse's own) plus two pinned research apps, `com.facebook.study` and `com.facebook.viewpoints`. Anyone else gets `"Caller Identity … is not trusted"`. The receiver requires an "auth" `PendingIntent` whose creator passes the same check. **Untrusted callers are rejected by the inspected checks**; this supports intended Family-of-Apps sharing, not an unconditional proof against every bypass. Other allow-listed certificates were not individually attributed, and the trusted-caller decompilation has unresolved branches ([`12-phone-id-provider.txt`](evidence-android/12-phone-id-provider.txt)).
- **`HatchVoiceInteractionService`**: can register as the phone's **default digital assistant** (long-press home / "assist" gesture).
- **`HatchXInstallReferrerReceiver`** + `AD_ID` + Facebook `analytics2` uploaders: standard Meta attribution and analytics.
- **Oxygen preloads SDK** (`com.facebook.oxygen.preloads…`): Meta's first-party SDK tied to its preloaded-app infrastructure.

**9.0 audit additions:**

- The on-device MCP server is in-process (`LocalMCPServer`/`LocalMCPClient` over JNI) with no socket or listen strings.
- **`libtrafficnts.so`** is new in 9.0: Meta network telemetry (bandwidth, congestion and reachability probes) with cell-ID and BSSID data structures. It starts only when the server flag `hatch_android_traffic_nts_v2.init_services_enabled` is on, and its compiled default is off. Muse hard-codes its radio-signal (cell ID/BSSID) provider and mobile prober off.
- **`PerfettoTraceReceiver`** is exported with no permission. Any installed app can make Muse load and start the Perfetto tracing SDK. Reading traces still needs a privileged consumer such as adb. Low severity.
- Analytics batches go to `graph.<domain>/logging_client_events` with a hard-coded consent value that takes no user input. The traced analytics calls carry metadata, not data-source content. Attribution sends the advertising ID, subject to a server setting ([findings data](evidence-updates/2026-09-27/08-spyware-audit-findings.json)).

## 8. Summary

Every data path below is built to end at the Meta-hosted VM, through one gateway: `client.invoke.result` carries command results and `client.data_source.publish` carries sync and backfill.

| Shipped capability / observation | Static evidence |
|---|---|
| Read & send SMS, bulk SMS backfill | `READ_SMS`/`SEND_SMS`, `SmsDataSource`, `SmsBackfillStrategy` |
| Read call history, backfill | `READ_CALL_LOG`, `CallLogDataSource`, `CallLogBackfillStrategy` |
| History backfill with **no app-level connection-date clamp identified** (9.0 audit), while Messages, Call Log and Health copy says "shared after you connect" | `data_source.backfill`, `DataSourcePublishPipeline.deliver`, strings `0x7f1206d5`, `0x7f1206d1`, `0x7f1206d3` (8.0 resource IDs, [`15-consent-retention-android.txt`](evidence-android/15-consent-retention-android.txt)) |
| Place phone calls | `CALL_PHONE`, `phone.dial` |
| Read exposed notifications from **all apps by default** and invoke available notification actions, subject to grants/filters | `NodeNotificationListenerService`, `NotificationSerializer`, `notifications.action`, default `ALL` |
| No app-level OTP conclusion; Android 15+ redaction applies to untrusted listeners | bounded keyword search plus Android platform documentation |
| Background location + geofence pushes, **no local category-gate check on crossings** | `ACCESS_BACKGROUND_LOCATION`, `LocationDataSource.publishNow`, `NodeHitlCatalog` (6 gated sources) |
| Remote `location.get` and geofence commands with **no Muse approval step**; Android location permission only (9.0 audit) | `NodeHitlCatalog.forCommand` returns null |
| Wi-Fi SSID/BSSID (only with the fine-location grant) + carrier published with **no local category-gate check**: in the background (8.0); on every app open with the gateway connected (9.0 audit) | `commands/network/NetworkStateHandlerKt.java`, `AuraProactiveSyncWorker`; 9.0 `NetworkStateDataSource` (`AppOpen`/`TRANSIENT`) |
| Server-returned baseline for unset categories: omitted/unrecognized field → `AUTO_ALLOW`; no cache → proactive deny. Unset reads allow; unset writes ask | `PermissionDefaultMode.fromWire`, `NodeHitlMode.defaultFor` |
| Per-source sync switch defaults on and nothing in the app turns it off; only per-category approval modes remain (9.0 audit) | `slv_data_source_<id>` read with default `true`; `HatchDataSourceRegistry.setUserEnabled` has no caller |
| 19 health-data category permissions, extended history/background access requested, proactive publishing code | Health Connect perms, `HealthSyncManager` → `client.data_source.publish` |
| Deleted messages "may stay in the agent's memory"; support access ends confidentiality; training fallback on | app strings; `HatchAiTrainingApi.DEFAULT_ENABLED = true` |
| Server-initiated commands | manifest: *"Execute server-initiated device commands…"* |
| Re-registers work after boot/update, subject to OS restrictions | `HatchBootReceiver` |
| Cross-app identity sharing with certificate allow-list checks | exported `FoaPhoneIdProvider` (`com.facebook.GET_PHONE_ID`) |

### Conclusion

**Editorial assessment:** the author calls the broad cloud-collection design “spyware by design.” The technical evidence establishes capabilities, approval paths and disclosure concerns, not malicious intent or inevitable upload. OS denial and app approval modes can prevent collection. Retention/training copy describes intended policy; actual records sent, backend use and deletion remain untested. Other people's data can be included, but their consent cannot be inferred from this audit.

**Limits:** static audit of the 8.0 APK plus the 9.0 follow-up; it found no hidden or covert collection channel and did not observe live traffic. The collection runs through the channels described above and is disclosed in consent text, except where noted: network-state reporting has no in-app disclosure, and backfill can reach history older than the "shared after you connect" copy suggests.

## 9. Remove it

1. Settings → Apps → Special app access → **Notification access** → turn Muse **off**.
2. Settings → Apps → Muse → Permissions → deny **SMS, Call logs, Phone, Location, Contacts, Calendar, Photos, Camera, Microphone, Nearby devices**. Use the Android controls: in 9.0 Muse's per-source sync switch has no working off path, and location is gated only by the Android permission.
3. Health Connect → App permissions → Muse → **Remove all** and delete Muse's data access.
4. Settings → Apps → Default apps → **Digital assistant app**: switch away from Muse if it was set.
5. Disconnect connectors and uninstall. Per the app's text, disconnecting prevents future syncing; deleting what was already shared is a separate request. Use Muse’s current account/data controls to request removal of previously uploaded data; this review has not verified a Muse-specific Accounts Center deletion workflow. Uninstalling does not demonstrate cloud deletion.

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

The **9.0 audit** notes in this file come from the 9.0.0.11.178 APK (sha256 `fc4e70f48915a86094329b8b1f5941ea6eccc78d1dfee1d7a73638e7162194e3`). Their smali locations, verifier votes and corrections are in [`08-spyware-audit-findings.json`](evidence-updates/2026-09-27/08-spyware-audit-findings.json), with DEX excerpts in [`07-android-bytecode-excerpts.txt`](evidence-updates/2026-09-27/07-android-bytecode-excerpts.txt).

---

*Static analysis only (apksigner, aapt2, jadx 1.x decompile). The app was never installed or run. Decompiled Meta code is not included in this repo; only short excerpts and grep output.*
