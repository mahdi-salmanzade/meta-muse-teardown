# Review log — 2026-09-24

[Reports](README.md) · [Complete evidence index](EVIDENCE.md)

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
