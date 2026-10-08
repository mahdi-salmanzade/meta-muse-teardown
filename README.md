![Muse privacy concern — independent teardown](assets/muse-platforms.png)

# Muse by Meta: what the clients can access

Independent privacy and security research into Muse on **macOS, Android and iOS**. We inspect the shipped apps, compare versions, test selected boundaries and publish the evidence—including corrections to our own findings.

**The concern:** connecting personal data to a cloud agent can allow both one-time reads and ongoing sync. The important questions are what it can read, which approvals apply, how much history it can request, and what remains after you disconnect. OS permissions can prevent access; a capability in the code is not proof that your data was uploaded.

[Findings](CROSS-PLATFORM.md) · [Version history](VERSIONS.md) · [What we did](RESEARCH-HISTORY.md) · [Methods](METHODS.md) · [All evidence](EVIDENCE.md)

## What matters on each platform

Latest inspected builds below. **Research updated 8 October 2026**; this is not a claim that these are the newest releases available today.

| Platform / inspected build | Main concerns | What changed since the earlier samples |
|---|---|---|
| **[macOS 6.0](MACOS.md)** | Local messages, mail and files; desktop control; ongoing connector sync; payment-key validation controlled by server inputs. | Removed the bundled browser extension and stealth script. Added connector switch UI and more desktop-control code. |
| **[Android 9.0.0.23.178](ANDROID.md)** | SMS, notifications, contacts, health and location; historical reads; some sources lack the app's category approval gate. OS gates still apply. | Permissions fell **65 → 61**; identified agent photo handlers were removed. This does not rule out all media attachment paths. |
| **[iOS 9.1.0](IOS.md)** | Photo-sync controls, health/location access, new Alo voice and wearable-recording code. | Adds voice/model-configuration and wearable paths; removes the identified Notes-export literals. **Third-party decrypted code is not authenticated.** |

## Latest investigations

- **Payment-key trust:** the Mac web client can skip validation of a card-encryption key's certificate chain through a server-deliverable flag or a response field. This is **not TLS verification**; the flag defaults false and production activation is unknown. [Finding and evidence](PAYMENT-AND-TRANSPARENCY-2026-10-08.md#1-the-ptt-payment-key-validation-switch).
- **Confidential VM verification:** newer mobile samples remove the Sigstore/Rekor proof path and retain Cloudflare Plexi auditor signatures. Plexi already existed and is public; the stronger claim that public transparency disappeared was rejected. [What changed](PAYMENT-AND-TRANSPARENCY-2026-10-08.md#2-cvm-attestation-transparency-what-v9-actually-changed).
- **Alo and wearable audio:** the iOS sample contains new voice and recording-upload paths. Captured `multimango.com` site code connects Mango to Muse, but does not establish its legal operator or prove user audio was uploaded there. [Investigation](ALO-AND-MULTIMANGO-2026-10-08.md).

These are follow-ups on the already inspected builds, not a new release audit.

## What we verified—and what we haven't

We checked package signatures and hashes, compared permissions and bundled components, traced selected code paths, and reviewed consent/retention copy. **Three older browser-extension behaviors were reproduced** in isolated Chromium: page metadata continued while paused, pause reset on restart, and the last command's parameters remained after unpairing. Those results apply to the extension bundled with Mac 3.0/4.1, which is absent from 6.0.

**Native Muse apps were not run.** We have no captured native production uploads or measured fresh-account defaults. Server retention, deletion, training use and production feature settings remain unresolved. iOS metadata signatures do not authenticate the decrypted instructions. [Methods and limits](METHODS.md) · [Next tests](RESEARCH-PLAN.md).

## Follow the research

- **Understand the problems:** [findings by concern](CROSS-PLATFORM.md), then the platform guides above.
- **See what happened:** [every inspected version](VERSIONS.md) and [investigation timeline](RESEARCH-HISTORY.md).
- **Check the work:** [76 evidence files](EVIDENCE.md), [reproduction instructions](METHODS.md#reproduce-the-work) and [correction log](REVIEW.md).
- **Read the background:** [why this project exists](ABOUT.md) and [archived detailed reports](reports/README.md).

App archives and full extracted code are excluded from Git. The banner is editorial artwork. Corrections are welcome: open an issue with the build, disputed claim and supporting evidence.

<a id="1-is-this-really-metas-app"></a><a id="10-if-you-already-installed-it"></a><a id="11-reproduce-it-yourself"></a><a id="12-current-public-disclosures-and-release-status"></a><a id="2-architecture-your-mac-as-a-node-for-a-meta-vm"></a><a id="3-what-it-can-read"></a><a id="4-what-it-uploads-in-the-background"></a><a id="5-full-computer-control"></a><a id="6-the-chrome-extension-broad-debugger-access"></a><a id="7-stealthminjs-a-bot-detection-evasion-kit"></a><a id="8-is-muse-spyware"></a><a id="contents"></a><a id="crash-reports-telemetry-and-updates-mac-41"></a><a id="documented-privacy-concerns"></a><a id="imessage-read-straight-from-the-database"></a><a id="limits"></a><a id="mail-notes-messages-via-applescript"></a><a id="metas-track-record"></a><a id="muse-by-meta-ios-macos-and-android-privacy-teardown"></a><a id="platforms-covered"></a><a id="training-and-approval-defaults"></a><a id="what-changed-in-this-review--2026-09-24"></a><a id="what-changed-in-this-review--2026-09-27"></a><a id="what-it-refuses"></a><a id="what-permission-does-and-does-not-establish"></a><a id="whatsapp-reading-another-apps-private-database"></a>

Earlier detailed sections and evidence tables are preserved in the [previous report](reports/README-BEFORE-RESTRUCTURE.md).
