# Findings by concern

[Overview](README.md) · [macOS](MACOS.md) · [Android](ANDROID.md) · [iOS](IOS.md) · [Version history](VERSIONS.md) · [Evidence](EVIDENCE.md)

Research through **8 October 2026**. This page connects the privacy questions across platforms. Each row names its version scope; the [older detailed capability matrix](reports/CROSS-PLATFORM-BASELINE.md) is preserved separately.

## How the data path works

A Muse client exposes local tools and sync sources to a cloud agent. A permitted command can read data and return a result; a permitted sync source can send updates or requested history. **OS grants, app approval settings, connector state and server configuration all affect the result.** Neither a tool name nor a permission declaration proves collection.

## The findings

| Concern | Where the evidence applies | What the research establishes | What remains unknown |
|---|---|---|---|
| **Breadth of personal access** | Original Mac 3.0, Android 8.0, iOS 8.1; later comparisons linked in the platform guides | Local tools cover sensitive sources, with different mechanisms and controls on each platform. Android's identified photo handlers are removed in 9.0.0.23. | Actual native payloads and the permissions a particular account grants. |
| **Ongoing sync and historical reads** | Mac 3.0/4.1/6.0, Android 8.0 and reviewed 9.x paths, iOS samples | Sync/backfill code is present. Mac 6.0 adds connector switches. Android time-series parsers show no connection-date clamp. iOS photo controls distinguish persistent settings from a temporary pause. | Production defaults, requested history depth and immediate enforcement after denial/revocation. |
| **Uneven app-level approvals** | Android 9.x; Mac approval/UI traces | Android's six mapped categories exclude location/geofence, network and battery. Mac policy has stored/server-controlled branches. OS gates still apply. | Exhaustive runtime gate coverage and fresh-account server responses. |
| **Other people's data** | Message, contact and notification connectors; iOS 9.1 wearable lead | Permitted access can include correspondents' information. New wearable-recording code raises a separate bystander-consent question. | Consent outside the account holder's prompts; wearable availability, recording behavior and actual uploads. |
| **Pause and unpair boundaries** | Browser Node bundled with Mac 3.0/4.1 | Local browser tests reproduce page metadata during pause, pause reset on restart, and retained last-command parameters after unpairing. | Production gateway handling. The component is absent from Mac 6.0. |
| **Deletion and training disclosures** | Captured platform copy and September public-source review | Copy says disconnection does not erase prior sharing and deleted messages may remain in agent memory. Connector footers discuss AI improvement. | Backend deletion, retention periods, which records enter training and opt-out enforcement. |
| **Diagnostics and identity** | Original platform inventory; Mac 4.1/6.0 follow-ups | Telemetry/diagnostic paths exist; selected Mac paths default on. Android attribution is server-gated. Shared identifiers/entitlements are capabilities, not proof of every cross-app exchange. | Real payload contents, scrubbing, enabled cohorts and server use. |
| **Payment encryption-key trust** | Strongest trace: Mac 3.0/4.1/6.0 web bundles | Flag or `devExternal` response can skip the key certificate-chain check. TLS is separate. | Production activation; Android's decompiled failure branch and iOS configuration wiring. |
| **Confidential VM proof verification** | Android 9.0.0.23 and iOS 9.1, compared with older samples | Sigstore/Rekor support removed; pre-existing public Plexi auditor-signature path retained. | Previous production proof selection, current enforcement policy and completeness of public log discovery. |
| **Voice and model configuration** | iOS 9.1 sample, compared with 8.1; October 8 public captures | New Alo path and conditional model-defaults fetch. Captured Mango site code connects the project to Muse. | Domain's legal operator, production rollout and user-content flows. |

## Check the supporting work

- **Access, approval and sync:** [macOS guide](MACOS.md), [Android guide](ANDROID.md), [iOS guide](IOS.md), [reviewed October comparison](V9-AUDIT-2026-10-06.md).
- **Browser observations:** [synthetic Chromium results](evidence-updates/2026-09-27/05-extension-browser-tests.json).
- **Retention/training copy:** [macOS](evidence/15-consent-retention-macos.txt), [Android](evidence-android/15-consent-retention-android.txt), [iOS](evidence-ios/15-consent-retention-ios.txt), [dated vendor comparison](evidence/15-public-statements-vs-app.txt).
- **Transport, telemetry and identity:** [original detailed analysis](reports/CROSS-PLATFORM-BASELINE.md#network-protocol-and-telemetry), qualified by the later platform guides.
- **October 8:** [payment and VM trust](PAYMENT-AND-TRANSPARENCY-2026-10-08.md), [Alo and wearable investigation](ALO-AND-MULTIMANGO-2026-10-08.md).

## Reading the strength of a claim

**Locally reproduced** means the behavior occurred in our isolated browser fixture. **Static** means the inspected artifact contains the cited code, configuration or text. **Public-source** means a captured page or service response supports the statement. **Unresolved** means the evidence cannot answer the question. A static finding does not become a runtime observation because several reviewers agree with it.

All iOS code-path claims inherit the third-party decrypted-sample limitation. Native apps were not run. See [methods](METHODS.md) for the evidence standard and [next tests](RESEARCH-PLAN.md) for how to resolve the open questions.

<a id="approval-model"></a><a id="consent-defaults-and-retention-what-the-apps-say"></a><a id="defaults-in-the-code"></a><a id="deletion-and-retention"></a><a id="muse-across-macos-android-and-ios"></a><a id="network-protocol-and-telemetry"></a><a id="one-pipe-to-a-meta-vm"></a><a id="summary-matrix"></a><a id="telemetry-ads-and-third-parties"></a><a id="transport-identity-and-persistence"></a><a id="transport-security"></a><a id="what-the-code-cant-tell-us"></a><a id="where-it-all-ends-up"></a><a id="where-your-data-goes-per-the-apps-own-footers"></a>

Earlier detailed sections and evidence tables are preserved in the [previous report](reports/CROSS-PLATFORM-BASELINE.md).
