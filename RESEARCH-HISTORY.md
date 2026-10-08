# What we did—and how the conclusions changed

[Overview](README.md) · [Version history](VERSIONS.md) · [Methods](METHODS.md) · [Correction log](REVIEW.md)

This is the investigation timeline. [Version history](VERSIONS.md) tracks changes in the apps; this page tracks changes in our understanding.

## 24 September: establish the baseline

**Work:** inspected Mac 3.0, Android 8.0.0.21.168 and a decrypted iOS 8.1 sample. Mapped tools, permissions, sync/backfill, approvals, transport, identity and consent/retention copy. Compared app wording with dated public statements and published bounded evidence extracts.

**Result:** broad, permission-dependent access and cloud-agent data paths on all three platforms. We corrected the Android health count and calendar/notification claims, distinguished Mail metadata from bodies, and documented iOS provenance limits. Static capabilities did not establish native uploads or universal OTP-filter failure.

**Read:** [original Mac report](reports/README-BEFORE-RESTRUCTURE.md), [Android report](reports/ANDROID-8.0-9.0.0.11.md), [iOS report](reports/IOS-8.1.md), [detailed cross-platform matrix](reports/CROSS-PLATFORM-BASELINE.md), [commit audit](COMMIT-AUDIT.md).

## 27 September: compare releases and test browser boundaries

**Work:** acquired/verified Mac 4.1 and Android 9.0.0.11.178, recorded an iOS listing discrepancy, compared packages, inspected selected Android DEX branches and exercised the older extension with 14 offline tests plus real isolated Chromium.

**Result:** reproduced page metadata during pause, pause reset after restart and retained command parameters after unpairing. Clarified Android app-open network publishing, permission checks and cached-policy defaults. No native Muse app or production account was used.

**Review changed the claims:** five iOS CMS signatures verify metadata, not decrypted instructions. Mac auto-sync is affected by stored/server state; display fallbacks are not production defaults. Permission denial can stop access. Missing iOS `processing` mode limits background-task claims. The Sparkle version alone does not prove an exploit. “Spyware by design” was separated from technical proof as an editorial judgment.

**Read:** [release/boundary report](RELEASE-AUDIT-2026-09-27.md), [dated privacy assessment](SPYWARE-VERDICT-2026-09-27.md), [independent corrections](TODAYS-CHANGES-AUDIT-2026-09-27.md).

## 6 October: compare the next Mac, Android and iOS samples

**Work:** inspected Mac 6.0, Android 9.0.0.23.178 and decrypted iOS 9.1. Independently checked signatures, feed tamper rejection, permissions, libraries, helpers, iOS metadata/pages and framework load commands. Repaired file-inventory parser errors and added regression fixtures.

**Result:** Mac removes the bundled extension/stealth script and adds connector switch UI. Android removes four media permissions and identified photo handlers. iOS adds Alo/wearable references and loses the identified Notes-export literals.

**Review changed the claims:** Wi-Fi SSID/BSSID are cleared without fine-location permission; unchanged command names do not prove unchanged implementations; several supposedly new iOS frameworks were already linked. New location entitlement and broad code searches are not evidence of bypasses or the absence of hidden behavior. Original finder ledgers were retained unchanged with corrections alongside them.

**Read:** [corrected build comparison](V9-AUDIT-2026-10-06.md), [independent review](TODAYS-CHANGES-AUDIT-2026-10-06.md), [verification evidence](evidence-updates/2026-10-06/11-independent-verification.json).

## 8 October: investigate voice, configuration and trust

**Work:** rechecked Alo/wearable offsets with an older iOS control, captured public Mango site/API material, catalogued per-client APIs, traced payment-key validation and checked Plexi's public keys/namespaces and an auditor signature.

**Result:** captured site code connects Mango to Muse, but does not establish legal ownership or user-content uploads. Payment-key validation can be skipped through two server-controlled inputs in the reviewed Mac web path; neither disables TLS. Newer mobile samples remove Rekor support and retain Plexi signatures.

**A stronger headline was rejected:** Plexi is public and pre-existed the newer builds. We cannot claim Meta replaced public transparency with a private system. Nor do we know whether the removed, staging-pinned Rekor path was ever selected in production.

**Read:** [Alo/Mango/wearable investigation](ALO-AND-MULTIMANGO-2026-10-08.md), [payment/VM investigation](PAYMENT-AND-TRANSPARENCY-2026-10-08.md), [12 new evidence files](EVIDENCE.md#follow-up-investigations--8-october-2026--12-files).

## 8 October: make the research readable

Replaced the crowded README with an overview; created consistent platform guides, a version history and methods page; separated current findings from historical detail. Preserved all four previous detailed pages as snapshots and kept all 76 evidence files unchanged. This was a documentation restructure, not a new release or runtime audit.

## Next: measure native behavior

The owner has a test device and throwaway account. Device identification and synthetic-only service setup remain to be completed. Native uploads, fresh-account policy, revocation, deletion and the audio/payment/VM questions are still open. The [research plan](RESEARCH-PLAN.md) defines the tests; none should be described as completed until results are recorded.
