# Muse for Android (`com.facebook.aura` 8.0.0.21.168)

The Android build of Meta's Muse agent. On a phone it goes further than the Mac app: **SMS, call log, every app's notifications, background location and 19 Health Connect data types**, with a "proactive sync" pipeline that publishes to Meta in the background once you allow a category.

← Back to the [main report](README.md) · Evidence: [`evidence-android/`](evidence-android/)

---

## 1. Authenticity

| Field | Value |
|---|---|
| File | `muse-from-meta-8-0-0-21-168.apk` |
| sha256 | `b351a83270b094d2ce565d239180bc226d7426c96d9de7575a47283af926c13d` |
| Package | `com.facebook.aura` (app label "Muse") |
| Version | `8.0.0.21.168` (versionCode `1061301140`), targetSdk 36 |
| Signer | `CN=Meta Platforms Inc., OU=Meta Mobile, O=Meta Platforms Inc., L=Menlo Park, ST=California, C=US` |
| Cert SHA-256 | `a16bbe0247a738bc8f09fef50d890dc177ec875a83a121f877329b1b89667e99` (RSA 4096, APK Sig Scheme v3) |
| Source Stamp | Verified, signed by Google (`CN=Android, O=Google Inc.`), meaning it was **distributed through Google Play** |

This is Meta's own Play Store build, not a repack ([`01-signature.txt`](evidence-android/01-signature.txt)).

## 2. Permissions

From the manifest ([`02-permissions.txt`](evidence-android/02-permissions.txt)):

| Category | Permissions |
|---|---|
| **SMS** | `READ_SMS`, `SEND_SMS` |
| **Calls** | `READ_CALL_LOG`, `CALL_PHONE` |
| **Location** | `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, **`ACCESS_BACKGROUND_LOCATION`**, `ACCESS_MEDIA_LOCATION` (GPS inside photos) |
| **Contacts / Calendar** | `READ_CONTACTS`, `WRITE_CONTACTS`, `READ_CALENDAR`, `WRITE_CALENDAR` |
| **Media** | `READ_MEDIA_IMAGES`, `CAMERA`, `RECORD_AUDIO`, `FOREGROUND_SERVICE_MICROPHONE` |
| **Health Connect** (19 data types + 2 access, see [`11-health-permission-count.txt`](evidence-android/11-health-permission-count.txt)) | steps, heart rate, **heart-rate variability**, resting HR, **sleep**, exercise, distance, calories (active + total), elevation, floors, **weight, body fat, body water mass, bone mass, lean body mass, height, basal metabolic rate, VO2 max**, plus **`READ_HEALTH_DATA_HISTORY`** and **`READ_HEALTH_DATA_IN_BACKGROUND`** |
| **Persistence** | `RECEIVE_BOOT_COMPLETED`, `FOREGROUND_SERVICE_SPECIAL_USE`, `WAKE_LOCK` |
| **Tracking** | `com.google.android.gms.permission.AD_ID`, install-referrer |
| **Other** | `BLUETOOTH_SCAN/CONNECT`, `ACCESS_WIFI_STATE`, `CHANGE_WIFI_MULTICAST_STATE`, `DETECT_SCREEN_CAPTURE`, `USE_BIOMETRIC`, `SET_ALARM` |

`READ_HEALTH_DATA_HISTORY` lets an app read health records **older than 30 days** (by default Health Connect only exposes the last 30 days). `READ_HEALTH_DATA_IN_BACKGROUND` lets it read them **while the app isn't open**.

## 3. "Execute server-initiated device commands"

Android requires foreground services of type `specialUse` to state their purpose in the manifest. Meta's own wording ([`03-manifest-components.txt`](evidence-android/03-manifest-components.txt)):

> **`NodeCommandService`**: *"Execute server-initiated device commands such as location queries and contact sync"*
>
> **`HatchForegroundService`**: *"Keep the app running in the background at the user's request to continue long-running assistant tasks"*

Commands arrive from Meta's gateway as `client.invoke` frames (`nodes/HatchNodeClient.java`). If Android blocks starting a foreground service, the app falls back to WorkManager (`"FGS start blocked, falling back to WorkManager: command="`). A `HatchBootReceiver` (exported, `BOOT_COMPLETED` + `MY_PACKAGE_REPLACED`) brings it back after every reboot and update.

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

Each category belongs to an approval ("human-in-the-loop") group in `nodes/core/NodeHitlGroup.java`: `SMS`, `SMS_SEND`, `CALL_LOG`, `PHONE_CALL`, `NOTIFICATIONS`, `LOCATION`, `HEALTH`, `PHOTOS`, `CONTACTS`, `CALENDAR`, … You approve by category, then the agent uses it. The **proactive sync** below goes through the same gate as `NodeHitlRequestKind.PROACTIVE_SYNC` (`nodes/datasource/ProactiveSyncRunner.java`). If no permission default is cached, `HatchNodeHitlGate` **fails closed to `ALWAYS_ASK`** ([`10-review-corrections.txt`](evidence-android/10-review-corrections.txt)). Once you pick "always allow" for a category, background publishing for it continues without further prompts.

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

When your health data changes, Muse notices and publishes it. `HealthSyncStartupJob` starts this at app startup.

**Location:**

> *"Current device location (lat, long, accuracy, address), read when the app is open, plus location pushes emitted when a user-registered geofence is crossed."*
> *"geofence broadcast receivers call publishNow() with the crossing coordinates."*

**Calendar:** `CalendarDataSource` sets `emitsProactively = true` and watches the calendar provider (`ProactiveTrigger.ContentObserver`, 5 s debounce), publishing events from 7 days back to 14 days ahead. Backfill runs in 30-day chunks.

**Notifications:** see §5.

**After reboot:** `HatchBootReceiver` enqueues a proactive-sync bootstrap, re-registers geofences, alarms and reminders, and logs `"Forced notification listener rebind via component-enabled toggle"`.

**Backfill** (bulk history import) exists for **SMS, call log, contacts and health**: `SmsBackfillStrategy`, `CallLogBackfillStrategy`, `ContactsBackfillStrategy`, `HealthBackfillStrategy`. SMS and call log take a `start_date` window (`"start_date is required for sms backfill"`). SMS keeps sync cursors `last_synced_sms_date_ms` and `recently_published_message_ids` and has a `readProactiveMessages` path.

## 5. The notification listener: every app, every message

`NodeNotificationListenerService` holds `BIND_NOTIFICATION_LISTENER_SERVICE`. Once you grant "Notification access", Android hands it **every notification posted by every app** ([`06-notification-listener.txt`](evidence-android/06-notification-listener.txt)).

The command description:

> *"Reports the device's current active notifications — app, title, body, sender, and the notification key used by `notifications.action`."*
> `notifications.action`: *"Operate on a device notification by key: reply to a message, dismiss one, dismiss all, or trigger one of its buttons."*

What `NotificationSerializer` pulls from each one:

```
android.title   android.text   android.bigText   android.textLines
android.messagingStyleUser     android.selfDisplayName   android.picture
MessagingStyle  InboxStyle  BigPictureStyle  CallStyle   app_package   category
```

`MessagingStyle` is how Signal, Telegram, WhatsApp, Messenger, Slack, Gmail and your bank's app show messages. It carries **sender names and message text**. `InboxStyle`/`textLines` carry multi-message email and chat summaries. `android.picture` is the attached image.

**Default: all apps.** From `gateway/store/HatchGatewayPrefsStore.java`:

```java
return strA01 != null ? PhoneNotificationsAccessMode.valueOf(strA01) : PhoneNotificationsAccessMode.ALL;
} catch (IllegalArgumentException unused) {
    return PhoneNotificationsAccessMode.ALL;
```

The only per-app filter (`BlockedAppsNotificationFilter`) blocks nothing in `ALL` mode, and in `SELECTED` mode blocks only apps **you** add to the list. A separate `WorkAppNotificationFilter` (with `WorkDeviceDetector` and `WorkNotificationFilterConfig`) filters work-profile and managed-device notifications. Meta built a dedicated filter for **employer data**, while **personal** notifications default to `ALL`.

**No 2FA protection.** A search for `otp`, `one-time`, `verification code`, `2fa`, `two-factor` across `commands/notifications` and `commands/sms` returns **no matches**. The app itself doesn't filter one-time codes. One mitigation: **Android 15+ can redact OTP content for untrusted notification listeners** at the OS level, so on newer phones some codes may reach Muse redacted. This keyword search doesn't cover obfuscated shared code or server-side filters.

`NotificationsDataSource` keeps a sync cursor (`last_synced_post_time_ms`, `recently_shipped`, `dedup_key`) and publishes through `client.data_source.publish` (`"Failed to publish notifications payload"`). The only off-switch in that path is `"Skipping notification publish: disabled by managed configuration"`, which is for MDM-managed devices.

## 6. Photos

`commands/photos` ([`08-photos.txt`](evidence-android/08-photos.txt)) contains:

- `MlKitPhotoLabeler`, `PhotoLabelScanner`, `PhotoLabelDatabase`: **on-device ML Kit labeling** of your gallery, cached in a local database so the agent can search photos by content.
- `PhotoUploadWorker`, `PhotoUploadDatabase`, `MediaDeviceSyncClient`: a background upload queue (`"Draining … queued photos"`, `"Uploaded photo "`) sending `original_filename`, `platform_asset_id` and the image.
- `photos.upload` accepts up to 50 photo IDs per call (`"photo_ids accepts at most 50 photos per call"`).
- `ACCESS_MEDIA_LOCATION` means the GPS coordinates embedded in photos are readable.

Unlike the Mac build's `MediaSync`, uploads here are agent-requested per batch, not a whole-library mirror. The labeling of the whole library happens on the device.

## 7. Other notable pieces

([`09-notable.txt`](evidence-android/09-notable.txt))

- **On-device MCP server + agentic runtime**: `libmcp_server_jni.so`, `libagentic_runtime_jni.so`, `libxplat_agentic_client_AgenticRemoteClientAndroid.so`, `libxplat_mcp-sdk_…__2025-06-18__mobileAndroid.so`. The phone speaks Model Context Protocol to the remote agent.
- **`assets/vmvnc/`** (noVNC `vnc.html` + `novnc-rfb.js`): a VNC viewer for watching the **cloud VM's desktop** from the phone.
- **`FoaPhoneIdProvider` + `FoaPhoneIdRequestReceiver`**: both **exported**, answering the `com.facebook.GET_PHONE_ID` intent with a Meta "Family of Apps" phone ID (`COL_PHONE_ID`, `COL_ORIGIN`, `COL_TIMESTAMP`). This is the cross-app identifier that links Muse to Facebook, Instagram, WhatsApp and Messenger on the same phone. Caller verification lives in an obfuscated parent class that wasn't reviewed.
- **`HatchVoiceInteractionService`**: can register as the phone's **default digital assistant** (long-press home / "assist" gesture).
- **`HatchXInstallReferrerReceiver`** + `AD_ID` + Facebook `analytics2` uploaders: standard Meta attribution and analytics.
- **Oxygen preloads SDK** (`com.facebook.oxygen.preloads…`): Meta's first-party SDK tied to its preloaded-app infrastructure.

## 8. Summary

| Capability | Proven by |
|---|---|
| Read & send SMS, bulk SMS backfill | `READ_SMS`/`SEND_SMS`, `SmsDataSource`, `SmsBackfillStrategy` |
| Read call history, backfill | `READ_CALL_LOG`, `CallLogDataSource`, `CallLogBackfillStrategy` |
| Place phone calls | `CALL_PHONE`, `phone.dial` |
| Read every notification from every app, reply as you | `NodeNotificationListenerService`, `NotificationSerializer`, `notifications.action`, default `ALL` |
| No OTP/2FA filtering | no matches for otp/2fa/verification code |
| Background location + geofence pushes | `ACCESS_BACKGROUND_LOCATION`, `LocationDataSource` publishNow on crossing |
| 19 health data types, history >30 days, background, proactive publish | Health Connect perms, `HealthSyncManager` → `client.data_source.publish` |
| Server-initiated commands | manifest: *"Execute server-initiated device commands…"* |
| Survives reboot | exported `HatchBootReceiver` on `BOOT_COMPLETED` |
| Cross-app Meta identity | exported `FoaPhoneIdProvider` (`com.facebook.GET_PHONE_ID`) |

## 9. Remove it

1. Settings → Apps → Special app access → **Notification access** → turn Muse **off**.
2. Settings → Apps → Muse → Permissions → deny **SMS, Call logs, Phone, Location, Contacts, Calendar, Photos, Camera, Microphone, Nearby devices**.
3. Health Connect → App permissions → Muse → **Remove all** and delete Muse's data access.
4. Settings → Apps → Default apps → **Digital assistant app**: switch away from Muse if it was set.
5. Uninstall. Then ask Meta, through Accounts Center, to delete what was already published.

---

*Static analysis only (apksigner, aapt2, jadx 1.x decompile). The app was never installed or run. Decompiled Meta code is not included in this repo; only short excerpts and grep output.*
