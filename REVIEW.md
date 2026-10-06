# Review log

[Reports](README.md) · [Complete evidence index](EVIDENCE.md)

## 6 October 2026 — report consistency follow-up

Applied the remaining presentation fixes after the independent review: updated the README's inspected-version table and latest-review links, marked older cross-platform tables and release listings as historical, moved Android's photo-removal notice into the Photos section, corrected the claim that no helpers are bundled, and narrowed unverified upload/opt-out and setter-absence statements. No new runtime or release claim was added. Evidence files are unchanged.

## 6 October 2026 — independent review of the v9 findings

Reviewed commit `3058622` and corrected the [v9 report](V9-AUDIT-2026-10-06.md), README and platform crosslinks. [Full corrections and verification](TODAYS-CHANGES-AUDIT-2026-10-06.md).

Verified Mac signatures/feed/helper differences and automatic-update startup calls, Android signatures/permissions/libraries and Wi-Fi permission checks, and five iOS CMS/page/resource checks plus direct framework/token comparisons. Corrected repeated consent/authenticity/default overclaims, false framework additions, unsupported hostname attribution and the claim that unchanged command names prove identical implementation. Preserved the original ledger, fixed inventory-parser defects and indexed all 64 evidence files. Native runtime behavior remains untested.

## 27 September 2026 — independent audit of today's changes

Reviewed all three of today's existing commits (`e48d3ac`, `46fd067`, `0b52220`). [Full review and verification](TODAYS-CHANGES-AUDIT-2026-09-27.md).

Corrected claims that permission only affects timing, backfill proves exfiltration, valid iOS metadata signatures authenticate decrypted code, camera-roll periodic background processing works, and the old Sparkle version proves exploitability. Preserved the author's privacy assessment as explicitly editorial. Also corrected Pause persistence wording, Crashpad's UUID changes, transparency-key trust, broad negative-search claims and the missing evidence-index entry.

Independently verified five iOS CMS signatures and their CodeDirectory bindings, page/special-slot/resource hashes, both Android transparency signatures and ordinary file digests, Mac helper byte differences and selected native functions. Negative controls reject modified signed content. All 14 offline extension tests and the real Chromium synthetic integration test pass again; the original seven release-evidence files regenerate identically. Native runtime behavior and production servers remain untested.

The original finder ledger remains unchanged. Added one verification script and one machine-readable evidence file, bringing the evidence manifest to 62 files.

## 27 September 2026 — release and boundary audit

The [new supplement](RELEASE-AUDIT-2026-09-27.md) adds verified Mac 4.1 and Android 9.0.0.11.178 samples. Mac signing and the production feed's Ed25519 signature pass; a one-byte-modified artifact fails. The Android APK's v3 signature/source stamp pass, its signer matches the baseline and all 65 declared permissions are unchanged. Apple's web listing shows iOS 9.0 while lookup returns 8.1; no 9.0 code was acquired.

The bundled browser extension is unchanged across the two Mac builds. Real isolated Chromium reproduces page-metadata transmission while paused, pause reset after browser restart, and retained last-command parameters after unpairing. Fourteen offline JavaScript tests also cover safeguards and pending/cached results across connection changes. Only synthetic data and a local gateway were used; production account isolation and server behavior remain untested.

Android DEX checks confirm the network-state source's app-open/transient delivery and connection-dependent runner path, plus distinctions between missing-baseline `ALWAYS_ASK` and unmatched wire-value `AUTO_ALLOW`. JADX reported 183 reconstruction errors; those are not runtime app exceptions. New native credential strings are leads, not proven fixes.

Seven evidence files and four reproduction helpers accompany the report. The original 53 evidence files are preserved. The owner has a test device and throwaway account; native testing remains pending identification of that device and synthetic-only service setup.

Validation: 14 unit tests pass for both Mac extension copies with identical results; the real Chromium assertions pass. A separate regeneration matches all seven new evidence files. All 60 evidence checksums, JSON, script syntax and local Markdown links pass.

## 24 September 2026 — original review

This review checked the three available samples, every tracked evidence file, the report claims and the reproduction script. It added public-source research and new reproducible extracts. Another task added iOS notes during the review; those files have been retained with their limits made explicit.

## Material additions and corrections

| Area | Updated finding | Supporting material |
|---|---|---|
| Current Mac release | Production feed lists the same 3.0 / 1075746581 build as the local sample | [Feed metadata](evidence/13-release-feed.json) |
| Mac email | Auto-sync copy distinguishes sender/subject metadata from message text | [Consent copy](evidence/07-autosync-consent-copy.txt) |
| Mac sync defaults | Consent initializer has a true fallback, but connector state is bridged to native code; universal/server-overridden defaults are unproved | [Review extracts](evidence/12-permission-and-pairing-review.txt) |
| Mac photo coverage | Background uploader is present; entire-library mirroring is not established by upload log strings | [Sync strings](evidence/05-sync-and-upload-strings.txt) |
| Browser pairing | Origin checks, gateway-host restrictions and WSS requirements were missing from the original discussion | [Review extracts](evidence/12-permission-and-pairing-review.txt) |
| Android health count | 19 category permissions plus 2 extended-access permissions | [Count/list](evidence-android/11-health-permission-count.txt) |
| Android proactive sync | Shared runner and direct notification publishing include approval-gate calls | [Code excerpts](evidence-android/10-review-corrections.txt) |
| Android calendar | Observer-driven publishing and calendar backfill were omitted from the initial overview | [Code excerpts](evidence-android/10-review-corrections.txt) |
| Android OTPs | Keyword absence cannot establish absence of filtering; platform redaction must be considered | [Bounded search](evidence-android/06-notification-listener.txt), [Android 15 documentation](https://developer.android.com/about/versions/15/behavior-changes-all) |
| iOS integrity | Signature verification fails; matching pages outside encrypted ranges do not authenticate decrypted code | [Raw verification](evidence-ios/01-provenance.txt), [earlier page-hash notes](evidence-ios/01-authenticity.txt) |
| iOS health | 110 imported type identifiers; not proof of 110 permissions granted or uploads | [Reproduced imports](evidence-ios/11-health-import-count.txt) |
| iOS Photos | Persistent sync toggle differs from a temporary pause; full-library override is explicitly described | [Tool/UI copy](evidence-ios/05-sync-and-consent.txt) |
| iOS messages | User-created Shortcuts forwarding; no historical Messages database read established | [Forwarding evidence](evidence-ios/06-sync-upload.txt) |
| iOS HomeKit | Accessory/scene and geofence-triggered action descriptions present, subject to permissions | [Tool excerpts](evidence-ios/05-agent-tools.txt) |
| Identity / trackers | Shared containers, identifiers and negative SDK searches do not prove particular transmissions or absence of tracking | [iOS notes](evidence-ios/10-notable.txt), [Android notes](evidence-android/09-notable.txt) |
| Research tooling | Mac script now checks integrity, cleans temporary mounts/copies and avoids a `head`/`pipefail` failure and fixes macOS BSD grep’s repetition-limit error; collector rebuilds new bounded extracts | [Scripts](scripts/) |

## Public sources checked

The main report’s [public-disclosures section](README.md#12-current-public-disclosures-and-release-status) distinguishes publisher statements from independently inspected local evidence. Sources accessed on 2026-09-24 include:

- [Meta launch announcement — 8 September 2026](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/)
- [Meta security/data-policy technical post — 8 September 2026](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse)
- [Meta Connect glasses announcement — 23 September 2026, Spanish](https://about.fb.com/ltam/news/2026/09/tu-agente-personal-llega-a-los-lentes-con-ia/) — indexed source excerpt; direct page fetch failed during this review
- [US App Store listing](https://apps.apple.com/us/app/muse-from-meta/id6760173601)
- [Mac production update feed](https://www.facebook.com/endo/release/appcast.xml?channel=production)
- [Android notification changes](https://developer.android.com/about/versions/15/behavior-changes-all) and [Health Connect history rules](https://developer.android.com/health-and-fitness/health-connect/read-data)
- [Chrome extension permissions](https://developer.chrome.com/docs/extensions/develop/concepts/declare-permissions)
- [Apple app groups](https://developer.apple.com/documentation/xcode/configuring-app-groups), [notification service extensions](https://developer.apple.com/documentation/usernotifications/unnotificationserviceextension) and [background pushes](https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app)
- Historical sources linked in the main report: ACCC, FTC, the original Local Mess researchers, The Register and MacRumors.

The supplied Assange wording is preserved near the banner and attributed to the journalistic summary, rather than misrepresented as a single verbatim sentence of his speech.

## What remains unverified

- Production connector defaults, feature-flag values, approval behavior and the data actually transmitted by each platform.
- The latest Android store-distributed build and whether newer account-specific rollouts differ from these samples.
- Cryptographic authenticity of the decrypted iOS instruction bytes; the original acquisition chain and the earlier page-hash verifier are not included.
- Server-side filtering, model-training sanitization, retention, backup deletion and rollout of Confidential VM.
- The login-gated Muse privacy-policy text. No authenticated session was used to retrieve it.
- Security implications of obfuscated code, dynamically constructed strings or behavior outside the inspected paths. No app was executed and no exploit was attempted.

## Validation performed

- Recomputed all three input archive hashes; they match the recorded sample hashes.
- Rechecked Mac code-signature integrity and Android APK v3/source-stamp verification; recorded the iOS verification failure.
- Regenerated the new local evidence into temporary directories and compared it with the committed extracts.
- Ran the Mac inspection script against the supplied DMG without launching the app.
- Checked Markdown file/anchor links, parsed JSON evidence, verified the evidence checksum manifest and checked the Git diff for whitespace errors.

The banner is a PNG conversion of the user-supplied HEIC. Image pixels were preserved by format conversion; embedded EXIF/text metadata was removed from the published PNG.
