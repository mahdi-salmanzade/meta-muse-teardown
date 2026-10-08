# macOS: broad local access, changing controls

[Overview](README.md) · [Versions](VERSIONS.md) · [Android](ANDROID.md) · [iOS](IOS.md) · [Evidence](EVIDENCE.md)

**Latest inspected: 6.0 / `1082791187`.** Bundle: `com.meta.endo`. Research through 8 October 2026. Native findings are static; the separate browser tests used synthetic data and a local gateway.

## What changed by version

| Inspected version | What we found | What it means now |
|---|---|---|
| **3.0 / `1075746581`** | Local-data tools, background-sync machinery, desktop/shell control, Browser Node 1.0.8 and a stealth script. | Establishes the original capability baseline. Access still depends on OS grants and app policy. |
| **4.1 / `1077426479`** | Signed update verified; all 20 bundled extension files match 3.0. Local browser tests reproduced pause/restart/unpair behavior. | The browser findings apply to both older bundles. |
| **6.0 / `1082791187`** | Bundled extension and stealth script removed; connector switch UI added; more screen/input-control references. | Two older components are gone. Native automation remains; the extension tests are not findings against a component shipped in 6.0. |

Sources: [original detailed report](reports/README-BEFORE-RESTRUCTURE.md), [4.1 comparison](RELEASE-AUDIT-2026-09-27.md), [6.0 audit](V9-AUDIT-2026-10-06.md#macos-60).

## Problems and controls

### Personal data can become cloud-agent input

The original tools cover iMessage and WhatsApp databases, Mail and Notes, contacts, calendars, reminders and files. Successful permitted reads can return results to the cloud agent. Sync/backfill paths can expand that beyond the item in a single request. Mail's sync copy distinguishes sender/subject metadata from bodies fetched on request.

Full Disk Access, Automation and other OS grants matter. The app lacks the App Sandbox entitlement, but that does not bypass macOS privacy controls or Unix permissions. [Access paths and consent](reports/README-BEFORE-RESTRUCTURE.md#3-what-it-can-read).

### Ongoing sync needs understandable controls

In 3.0/4.1, Calendar, Reminders and Contacts had no dedicated in-app auto-sync switch in the reviewed paths. Stored state and server configuration affected sync; the fallback was off. **6.0 adds per-connector switch UI and native bridge references.** A web `?? true` fallback does not prove every connector starts enabled. Whether denial immediately stops every queued action still needs device testing. [6.0 findings](V9-AUDIT-2026-10-06.md#static-findings-retained-from-the-ledger).

### Desktop control increases the consequence of an approval mistake

The clients contain screen capture, keyboard/mouse automation and shell-command tools. 6.0 adds ScreenCaptureKit/`SCStream` references and finer input primitives. Persistent approvals and instructions to preview sensitive actions deserve testing: model instructions alone do not establish enforcement. No unrestricted control of every protected surface was demonstrated. [Computer-control review](V9-AUDIT-2026-10-06.md#static-findings-retained-from-the-ledger).

### Payment-key validation is optional in the reviewed web path

The 3.0/4.1/6.0 web bundles contain a default-false, server-deliverable flag that skips the certificate-chain check for a payment encryption key. A `devExternal` response field independently skips that check. The reviewed checkout defaults to LIVE, and no client-side production guard was identified. **TLS remains intact; production activation and card-data theft were not demonstrated.** [Payment investigation](PAYMENT-AND-TRANSPARENCY-2026-10-08.md#1-the-ptt-payment-key-validation-switch).

### Diagnostics and updates have separate questions

Reviewed older crash-upload code returns enabled, with no ordinary-user opt-out found in those paths. 6.0 adds reliability/MetricKit references; actual native payloads and coverage remain unmeasured. Startup code enables automatic update checks/downloads, while feed signatures and tamper rejection verify. The bundled Sparkle version merits follow-up, but no exploitable Muse updater vulnerability was reproduced. [Diagnostics and updater review](V9-AUDIT-2026-10-06.md#macos-60).

## What we reproduced in the older extension

| Test in isolated Chromium | Observed result | Scope |
|---|---|---|
| Pause, then navigate a synthetic page | Fresh commands blocked; URL/title metadata still reached the local gateway | Browser Node bundled with 3.0/4.1 |
| Restart the browser after pausing | Pause state reset | Same extension |
| Unpair after a synthetic command | Auth token cleared; last command's parameters remained locally | Same extension |

[Browser evidence](evidence-updates/2026-09-27/05-extension-browser-tests.json) · [Full boundary report](RELEASE-AUDIT-2026-09-27.md). These tests did not contact a production Meta gateway.

## What we did and what remains

Verified package/signing metadata, the signed update feed and tamper rejection; compared resources, entitlements and helpers; traced selected native and web branches; ran the older extension tests. [Methods](METHODS.md) explains reproduction.

Still needed: fresh-account defaults, denied/allowed native connector tests, actual diagnostic payloads, payment flag/response behavior and server-side deletion effects. [Device test plan](RESEARCH-PLAN.md).
