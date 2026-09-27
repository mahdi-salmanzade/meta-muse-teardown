# Audit of today's changes — 27 September 2026

[Reports](README.md) · [Evidence](EVIDENCE.md) · [Independent results](evidence-updates/2026-09-27/09-independent-verification.json)

Reviewed commits `e48d3ac`, `46fd067` and `0b52220`, from the 24 September baseline `fbb05d8`. The working tree was clean at the start. The image-caption edit in the conversation is not a repository change.

**Result:** the browser findings reproduce, and several integrity claims verify. The later prose overstated what permission gates, backfill code, iOS signatures and dependency versions establish. Those claims are corrected across the main, platform, cross-platform and verdict reports. The author's “spyware by design” wording remains explicitly an editorial privacy assessment, not a technical finding of covert collection or inevitable upload.

## Material corrections

| Priority | Finding in today's changes | Correction and basis |
|---|---|---|
| High | Consent “decides when, not whether” data reaches Meta; every Allow means a copy | Deny paths can prevent access. Approval does not prove successful execution or transmission. The existing Android DEX excerpts include fail-closed baseline and proactive-denial paths. Allowed commands can fail or return empty/filtered results. |
| High | Historical backfill called confirmed “undisclosed exfiltration” for all five sources | No transmission was observed. Calendar and Contacts disclose existing information. Messages, Call Log and Health wording is ambiguous about sharing time versus record age; the prompt can display the requested date window. No app-level connection-date clamp was identified in the reviewed path, but Health Connect's OS history restrictions still apply. Both earlier verifier notes included these qualifications. |
| High | iOS described as an “Apple-signed original” with only a minor decryption caveat | CMS signatures, signed CodeDirectory binding, special slots and unchanged pages verify. Decrypted instructions do not. Four nested executable resource hashes mismatch as well. Whole-app integrity still fails; modifications inside decrypted ranges cannot be ruled out. |
| Medium | Periodic camera-roll background processing presented as operational | The signed Info.plist lacks `processing` in `UIBackgroundModes`. The BGProcessingTask identifier alone does not authorize execution. Apple's scheduling requirements support a likely failure; no runtime scheduling test was performed. |
| Medium | Old Sparkle build treated as a proven exploitable vulnerability | The version and upstream hardening are verified, but this custom bundle has no XPC service bundles. The remaining Autoupdate scenario has deployment and privilege preconditions. No exploit was executed. |
| Medium | Browser Pause “held in memory only”; automatic re-pairing asserted as successful | Pause is cached in `_cachedStatus` but not restored. Browser restart resets it in the test. The standalone pairing path can request fresh credentials after Disconnect, but success depends on the production server, which was not tested. |
| Medium | Crashpad differs only in signature; unchanged tool names imply unchanged behavior | Crashpad also has eight changed UUID bytes. Other compared helpers differ only in signatures. An unchanged name set does not prove unchanged implementation; the same finder ledger reports computer-control changes. |
| Medium | Transparency signatures treated as a separate provenance guarantee | Both JWT signatures and 41/44 ordinary file hashes verify. Their embedded certificate differs from the APK signer. The outer APK authenticates the packaged JWT; the transparency key was not independently compared with an official-store trust anchor. The custom manifest digest was not reimplemented. |
| Medium | Negative searches become universal absence claims | Narrowed assertions about identifier APIs, downloaded code, hidden payloads, revocation and remotely changeable text. Container accounting is not proof of harmlessness; a name search is not exhaustive data-flow analysis. |
| Low | Evidence index still lists 60 files and omits today's finder ledger | Indexed the preserved finder ledger and the new independent verification, bringing the manifest to **62 files**. |

The original finder JSON is retained unchanged for traceability. Its raw titles and rubric labels include superseded interpretations. Reviewer votes are not a substitute for code, signatures or observations.

## Verification performed

### Browser and release evidence

- Reran all **14 offline extension tests**; output matches the committed results exactly.
- Reran the **real Chromium integration test**, using an empty temporary profile, synthetic pages and a loopback gateway. Paused metadata delivery, pause reset after browser restart and retained typed command parameters after unpairing all reproduce. No production pairing/account-isolation claim follows from this fixture.
- Regenerated the original seven release-evidence files into a separate directory and compared them with the committed files. Mac code-signature, notarization assessment and feed-signature checks pass; the changed-DMG negative control is rejected. APK signature/source-stamp checks pass.
- Browser timestamps and tab IDs vary on rerun; assertions and source hashes are the comparison targets. Original captured evidence was preserved.

### iOS CMS, page hashes and resources

The new [verification script](scripts/verify-september27-audit.py) reads the five Mach-O members directly from the IPA. It verifies each CMS against Apple roots from the macOS system keychain and checks that the authenticated hash-agility attribute binds the SHA-256 CodeDirectory. Altered signed content fails verification. No revocation lookup or app execution is performed.

After normalizing only the `cryptid` header field for comparison, page mismatches remain wholly within FairPlay ranges: 17,600 in the main binary, and 224, 108, 36 and 136 in the other binaries. This is consistent with decryption, but cannot authenticate or exclude changes within those ranges. Checked Info.plist, requirements, resource-seal and entitlement slots match.

Ordinary sealed resource hashes match (44/92/87/469/2 entries for the five respective bundles). The main seal additionally has four mismatched nested executables, each separately checked at the CMS/page level. No bytes trail the five signature regions. Account metadata and omitted resources are outside this authenticity claim and are not published.

The background modes are `audio`, `fetch`, `location` and `remote-notification`; **`processing` is absent**. The camera-roll task identifier is present. Apple documents a missing required background mode as a reason for `notPermitted`. This supports a static scheduling concern, not a measured failure. [Processing-mode requirement](https://developer.apple.com/documentation/backgroundtasks/bgprocessingtask), [scheduling error](https://developer.apple.com/documentation/backgroundtasks/bgtaskscheduler/error/code/notpermitted).

### Android transparency and backfill

Both packaged RS256 signatures verify and reject an altered message. All 41 DEX/native-library files are covered; 41 and 44 ordinary file digests respectively match. Both JWTs use certificate SHA-256 `004744571490c70869ec18051ae715d0c581b8e162dc1658b489016ca1257976`, distinct from APK signer `a16bbe0247a738bc8f09fef50d890dc177ec875a83a121f877329b1b89667e99`. This distinction is recorded rather than silently equating the trust anchors.

Re-read SMS and Health backfill parsing and the existing gate/runner DEX evidence. A supplied date is not a grant of access. Health Connect normally limits historical access relative to the first permission grant; extended history requires its own permission. No account was used to determine actual requested windows or returned records. [Android history restrictions](https://developer.android.com/health-and-fitness/health-connect/read-data).

### Sparkle and helper differences

The shipped framework reports **2.7.0-beta.1, build 2040**. Sparkle's maintainer documents client-validation hardening in the 2.7.2/2.7.3 releases. No `.xpc` bundles are present in this Muse package, so scenarios requiring those bundled services cannot simply be assumed. The Autoupdate race described upstream requires the helper to run with elevated privileges and package-install support. The installed-update path and exploitability were not exercised. The maintainer also warns against deploying 2.7.2 itself because of a subsequent crash fix. [Release](https://github.com/sparkle-project/Sparkle/releases/tag/2.7.2), [maintainer's preconditions](https://github.com/sparkle-project/Sparkle/discussions/2764).

Parsed Mach-O signature and UUID ranges and compared complete helper bytes. Sparkle, Autoupdate and Updater have zero differences outside signatures. Crashpad has **eight** differing bytes outside signatures, all inside its UUID. The earlier “signature only” sentence was incorrect for Crashpad.

Re-read the Mac auto-sync resolver and crash-provider enabled function with LLDB disassembly, without launching the target. The resolver includes the recorded stored-value/configuration branch, and the crash-provider function returns true. Those facts do not measure actual upload content or production flag values.

## Reproduce and remaining limits

With the saved packages/extractions and macOS/OpenSSL tools described in the [release audit](RELEASE-AUDIT-2026-09-27.md):

```bash
python3 scripts/verify-september27-audit.py
shasum -a 256 -c evidence.sha256
```

The release audit documents the separate unit/browser test commands. The independent script publishes hashes, bounded excerpts, disassembly and check outcomes; it does not publish the IPA, complete source, credentials or FairPlay account metadata.

This is a review of today's changes and targeted verification of material claims, not a new exhaustive audit of every native instruction. The earlier ledger's remaining native analyses are attributed static findings, not independently reproduced runtime behavior. No native app was launched, no live Meta account used, no privileged update raced, and no iOS 9 sample acquired. Production defaults, actual uploads, server-side retention/deletion, training use and server enforcement remain open.
