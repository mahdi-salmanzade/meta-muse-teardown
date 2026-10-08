# Android: sensitive sources, uneven app-level approvals

[Overview](README.md) · [Versions](VERSIONS.md) · [macOS](MACOS.md) · [iOS](IOS.md) · [Evidence](EVIDENCE.md)

**Latest inspected: 9.0.0.23.178.** Package: `com.facebook.aura`. Research through 8 October 2026. These are static code and package findings; native uploads were not observed.

## What changed by version

| Inspected version | What we found | What it means now |
|---|---|---|
| **8.0.0.21.168 / `1061301140`** | 65 declared permissions; SMS, call-log, notification, health, location and photo paths; background sync/backfill. | Original baseline for capabilities and consent review. Declared permissions are not granted access. |
| **9.0.0.11.178 / `1061401140`** | Same 65 permissions and matching signer. Selected DEX checks identify app-open/transient network and battery publishing. | Corrects the older network-source scheduling description; this path is not continuous boot-time publishing. |
| **9.0.0.23.178** | **61 permissions**, four media permissions removed; identified photo-handler package and registrations removed; 36 native libraries unchanged. | A material reduction in the identified photo capability. Other attachment/camera paths are not ruled out. |

Sources: [original Android detail](reports/ANDROID-8.0-9.0.0.11.md), [September comparison](RELEASE-AUDIT-2026-09-27.md), [October comparison](V9-AUDIT-2026-10-06.md#android-90023178).

## Problems and controls

### A category approval does not cover every source

The mapped categories are Health, Contacts, Calendar, Call Log, SMS and Notifications. Location/geofence, network and battery paths lack that same mapping in the reviewed code. This is a difference in **Muse's app-level approval**, not an OS permission bypass. Location authorization still applies; the network helper clears SSID/BSSID without fine-location permission. [Reviewed approval and network findings](V9-AUDIT-2026-10-06.md#privacy-findings-and-qualifications).

### Some unset read decisions depend on a cached server baseline

An omitted or unknown value in a parsed default-policy response normalizes to `AUTO_ALLOW`. That cached baseline can affect categories without a saved user choice. **Missing cache/fetch failure can fail closed**, and explicit user choices or a cached ask policy still matter. The production response and first-install experience were not tested. [Policy trace and corrections](RELEASE-AUDIT-2026-09-27.md).

### Historical data can exceed the period since connection

Reviewed time-series requests take a start date with no app-level clamp to the connector's connection date identified. Contacts can enumerate the accessible address book. Calendar and Contacts copy disclose existing data, so this is not a finding that all historical access is hidden. OS permissions, available records and Health Connect history rules bound results. [Backfill review](V9-AUDIT-2026-10-06.md#privacy-findings-and-qualifications).

### Notification access also concerns other people

The app's selection setting defaults to `ALL`; notification-listener, filtering and approval paths are present. Other people's messages may be included when access is permitted. `ALL` does not prove delivery of every field: OS redaction, device/profile policy and app filters can limit content. OTP-style notification handling needs controlled testing across Android versions. [Original listener analysis](reports/ANDROID-8.0-9.0.0.11.md).

### Photo access changed substantially

9.0.0.23 removes `ACCESS_MEDIA_LOCATION`, `READ_EXTERNAL_STORAGE`, `READ_MEDIA_IMAGES` and `READ_MEDIA_VISUAL_USER_SELECTED`, plus the identified agent photo handlers and associated label-scanning code. A flag alone cannot restore removed handlers. **The earlier photo analysis describes older builds.** [Removal evidence](evidence-updates/2026-10-06/11-independent-verification.json).

### Payment and confidential-VM code need narrow claims

Android has analogous payment-key validation machinery, but the decompiler marks the failure path incorrect; its exact hard-fail behavior is unresolved. Newer mobile code removes Sigstore/Rekor proof support while retaining the pre-existing, public Plexi auditor-signature path. Neither observation proves a production exploit or the end of public auditability. [October 8 investigation](PAYMENT-AND-TRANSPARENCY-2026-10-08.md).

## What we did and what remains

Checked APK signatures/source stamps and signer continuity; compared manifests, DEX descriptors and native libraries; inspected selected DEX instructions where decompilation was unreliable; mapped approvals, backfill and disclosures. [Methods](METHODS.md).

Still needed: observed fresh-account policy, denial/revocation tests, actual network/battery and notification payloads, historical-read boundaries and deletion behavior. Boot restoration of previously configured work is code evidence, not proof of unrestricted persistence. [Device test plan](RESEARCH-PLAN.md).

<a id="1-authenticity"></a><a id="10-reproduce-the-android-checks"></a><a id="2-permissions"></a><a id="3-execute-server-initiated-device-commands"></a><a id="4-proactive-sync-data-published-in-the-background"></a><a id="5-the-notification-listener-broad-access-with-filters-and-os-limits"></a><a id="6-photos"></a><a id="7-other-notable-pieces"></a><a id="8-summary"></a><a id="9-remove-it"></a><a id="commands-the-server-can-invoke"></a><a id="conclusion"></a><a id="muse-for-android-comfacebookaura-80021168"></a><a id="training-deletion-and-support-access-app-text"></a><a id="which-background-paths-the-gate-actually-covers"></a>

Earlier detailed sections and evidence tables are preserved in the [previous report](reports/ANDROID-8.0-9.0.0.11.md).
