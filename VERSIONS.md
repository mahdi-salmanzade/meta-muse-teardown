# Version history: what changed in the inspected builds

[Overview](README.md) · [Findings](CROSS-PLATFORM.md) · [What we did](RESEARCH-HISTORY.md) · [Evidence](EVIDENCE.md)

**Last research: 8 October 2026.** Dates below are research/check dates, not necessarily release dates. Version numbers differ across platforms; “v9” in the older report title names a research batch, not a shared product version. Builds not listed here were not audited.

## macOS

| Inspected | Build | Findings / changes | Verification and report |
|---|---|---|---|
| 24 Sep | **3.0 / `1075746581`** | Original local-data/sync/control baseline; Browser Node 1.0.8 and stealth script bundled. | Meta Developer ID, signature and recorded notarization checks. [Detailed baseline](reports/README-BEFORE-RESTRUCTURE.md). |
| 27 Sep | **4.1 / `1077426479`** | Same 20 extension files. Pause metadata, restart reset and post-unpair parameter persistence reproduced in a local browser fixture. | Signed DMG/feed validation and tamper rejection. [Release audit](RELEASE-AUDIT-2026-09-27.md). |
| 6 Oct | **6.0 / `1082791187`** | Extension/stealth script removed; connector switch UI and expanded screen/input code added. One location entitlement added, not an OS permission bypass. | Package/feed and helper comparisons; selected disassembly. [6.0 report](V9-AUDIT-2026-10-06.md#macos-60). |

**Current interpretation:** broad native automation and sync concerns remain; the earlier bundled-extension findings should not be attributed to a component shipped in 6.0. [macOS guide](MACOS.md).

## Android

| Inspected | Build | Findings / changes | Verification and report |
|---|---|---|---|
| 24 Sep | **8.0.0.21.168 / `1061301140`** | 65 permissions; sensitive data tools, sync, backfill and agent photo handlers. | Signature/manifest inspection and source traces. [Detailed baseline](reports/ANDROID-8.0-9.0.0.11.md). |
| 27 Sep | **9.0.0.11.178 / `1061401140`** | Still 65 permissions. Network/battery sources use app-open/transient publishing; approval-policy distinctions checked in DEX. | Matching signer/source stamp; bounded bytecode verification. [Release audit](RELEASE-AUDIT-2026-09-27.md). |
| 6 Oct | **9.0.0.23.178** | Permissions **65 → 61**; four media grants and identified photo handlers removed. 36 native libraries unchanged. Other sensitive sources/approval questions remain. | APK signature, permission/library comparison, Wi-Fi permission branch checks. [9.0.0.23 report](V9-AUDIT-2026-10-06.md#android-90023178). |

**Current interpretation:** the photo capability was reduced, while category-gate coverage, history and server-provided read defaults remain important. [Android guide](ANDROID.md).

## iOS

| Inspected | Build | Findings / changes | Verification and report |
|---|---|---|---|
| 24 Sep | **8.1.0 / `1074192126`** | Photo sync, health/location/HomeKit, Shortcuts forwarding and Notes-export implementation. | Third-party decrypted IPA. Later CMS checks verify metadata, not decrypted instructions. [Detailed baseline](reports/IOS-8.1.md). |
| 27 Sep | **9.0 — listing only** | Apple web listing and lookup disagreed. **No code comparison.** | Public metadata snapshot. [Release check](RELEASE-AUDIT-2026-09-27.md#1-releases-and-provenance). |
| 6 Oct | **9.1.0 / `1080826056`** | Alo voice, wearable-recording and model-defaults references added; identified Notes-export literals removed. Health import count remains 110. | Third-party decrypted IPA; CMS/page/resource, import and direct framework comparisons. [9.1 report](V9-AUDIT-2026-10-06.md#ios-910--decrypted-sample). |

**Current interpretation:** the voice/wearable additions deserve device testing. Import counts and signed metadata do not prove authenticated behavior or observed collection. [iOS guide](IOS.md).

## 8 October: deeper analysis of the same builds

These investigations added findings, not new app versions:

- **Alo / Mango / wearable:** rechecked offsets and older-sample controls; captured public site/API material connecting Mango to Muse. Legal operator, rollout and actual content flows remain open. [Report](ALO-AND-MULTIMANGO-2026-10-08.md).
- **Payment-key validation:** traced the server-deliverable flag and independent `devExternal` condition in the Mac web path. The check concerns the card-encryption key, not TLS. [Report](PAYMENT-AND-TRANSPARENCY-2026-10-08.md#1-the-ptt-payment-key-validation-switch).
- **VM transparency:** compared proof implementations and verified a public Plexi auditor signature. Removal of Rekor support does not establish a switch from public to private infrastructure. [Report](PAYMENT-AND-TRANSPARENCY-2026-10-08.md#2-cvm-attestation-transparency-what-v9-actually-changed).

For the investigation sequence, rejected claims and corrections, read [what we did](RESEARCH-HISTORY.md). For hashes, use the [complete evidence index](EVIDENCE.md).
