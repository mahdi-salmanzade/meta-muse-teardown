# Audit of today's findings — 6 October 2026

> **Dated research.** Findings below apply to the named samples and checks. For later changes and the current interpretation, see [version history](VERSIONS.md) and [research history](RESEARCH-HISTORY.md).

[Corrected report](V9-AUDIT-2026-10-06.md) · [Evidence index](EVIDENCE.md) · [Independent results](evidence-updates/2026-10-06/11-independent-verification.json)

Reviewed commit **`3058622f65ce01b321a9159904f05dfee8e2e882`**, its eight changed files, the underlying finder/verifier ledger, the saved packages and targeted source/disassembly. The working tree was clean at the start. This is a review of today's report and its material claims, not a new exhaustive reconstruction of every native path.

**Result:** the principal package changes hold up. Mac removes the bundled extension, Android removes four media permissions and the identified photo handlers, and the decrypted iOS sample adds voice/wearable code. Several summaries overstated authenticity, runtime behavior or the scope of a comparison. The corrected report keeps the privacy concerns while making those distinctions explicit.

## Material corrections

| Priority | Original claim | Review result |
|---|---|---|
| High | Permission decides “when, not whether”; every read is copied | Permission denial and app policy can block access. An allowed or reachable operation is not proof of completed transmission. This reintroduced a claim corrected on 27 September. |
| High | “All three samples are authentic”; no hidden payload/channel/injection | Mac and Android signatures verify. iOS signatures authenticate CodeDirectories and checked metadata, but not decrypted instructions. Negative searches cannot establish universal absence of hidden behavior. |
| High | Mac sync and AI training “default on” from `?? true` | These expressions occur in UI initialization/display. The connector's supplied state, native branches and actual server response matter. Training preference mutation is a separate path; the fallback does not establish training use or the account default. |
| High | Android app-open SSID/BSSID collection needs only network-state access | The Wi-Fi helper explicitly clears both identifiers without fine-location permission and filters unknown/scrubbed values. Original DEX instructions corroborate the Java reconstruction. Other network/battery fields still have an app-open publishing path. |
| Medium | New iOS frameworks include Speech, CoreBluetooth, CallKit, CryptoKit and Vision | Those were already linked. Direct load-command comparison adds only CoreML and the Swift CallKit library; PDFKit and Symbols are removed. New imported APIs were mistaken for new dependencies. |
| Medium | Collection table is byte-identical; no new data-pull command exists | The cited comparison is of selected literals, not implementation/table bytes. Unchanged names cannot prove unchanged behavior or exhaustively exclude new actions. |
| Medium | `multimango.com` is non-Meta and the old Mac mystery is resolved | The iOS model-defaults URL is present. Ownership and the old Mac path's purpose remain unverified. No user-content upload to that host was observed. |
| Medium | Missing Sparkle plist keys mean auto-update settings are not statically provable | Native startup calls both automatic-check and automatic-download setters with true. That does not prove successful installation, an unchangeable policy or a working exploit. |
| Medium | Blanket backfill disclosure failure, no-prompt comparisons and all-app notification coverage | Restore existing-data disclosure, cached/user policy, Health Connect restrictions and notification filtering qualifications. No production prompt/traffic test was performed. |
| Medium | HealthKit import location authenticates immediate delivery/raw upload; every iOS path has node HITL | 110 imports are verified. Imports do not prove behavior or grants. Voice, wearable pairing and node commands have distinct gates; universal enforcement was not established. |
| Medium | Older iOS report denied all microphone capture; old Android count became “wrong” | The older iOS report explicitly distinguished agent commands from user-initiated mic capture. The Android 65-permission count remains correct for its dated sample. |
| Medium | Inventory end-marker searches justify clean-container conclusions | PNG substring search could stop inside payload; JPEG last-marker search could hide appended material. Oversized MP4/Mach-O regions were not rejected. Fixed bounds/PNG parsing, made JPEG explicitly unverified, and added SHA-1 seal checking. |
| Low | Complete evidence index still lists 62 files | Added the original October ledger and the independent verification; all **64** evidence files are now indexed and checksummed. |

The original `10-v9-audit-findings.json` is retained unchanged. Its votes, labels and narrative include superseded interpretations; the corrected report and this review take precedence.

## Independent verification

### macOS

- Mac 6.0 archive SHA-256 matches the original ledger. Deep/strict signatures pass; Gatekeeper reports a notarized Meta Developer ID. The saved appcast signature verifies under the pinned key, and a one-byte-altered DMG is rejected.
- The older extension has **20 files**; the 6.0 directory is absent. `stealth.min.js` is also absent. Only the location entitlement is added.
- Four helpers have no changes outside UUID/signature regions. Sparkle remains 2.7.0-beta.1 / 2040, with no `.xpc` bundles.
- LLDB disassembly, without launching the target, records the proactive-sync configuration branch and the updater calls. Selector references at `0x10125a518` and `0x10125a520` resolve to the two automatic-update setters; helper `0x10069dacc` supplies `w2=1`.
- Original bundled JavaScript excerpts preserve the sync guard and training display fallback. Readable prepared-source excerpts are supporting evidence, with both source and original bundle hashes.
- Revised inventory: **316 entries**, 296 matching local seals, 18 unsealed entries and 2 nested-code references. No seal mismatch or trailing bytes in successfully parsed entries; one JPEG is explicitly unverified. These are accounting results, not a malware verdict.

### Android

- APK signature/source-stamp checks pass and the signer matches the earlier package. Both packaged transparency signatures verify and reject altered messages. Ordinary file hashes match; the custom manifest digest is not independently reimplemented, and the embedded transparency certificate is not the APK signing certificate.
- Permissions: **65 → 61**, exactly the four reported media permissions removed and none added. All **36 native libraries** match byte-for-byte. Photo-package descriptor markers disappear from the compared DEX files.
- Re-read cached approval-default and source-mapping code. Re-disassembled the Wi-Fi helper from the current APK to verify the fine-location check and nulling branches independently of JADX's Java output.

### iOS

- All five CMS signatures verify to Apple roots; signed attributes bind the SHA-256 CodeDirectories. Tampered signed content is rejected. Checked special-slot hashes match.
- After normalizing only `cryptid` for page comparison, mismatches remain inside FairPlay ranges: **17,932** pages in the main binary and **224 / 124 / 36 / 136** in the notification/widget/share/MobileConfig binaries. No mismatches occur outside those ranges. Four nested executable resource hashes mismatch. This is consistent with decryption, not proof those plaintext ranges were otherwise unmodified.
- Compared load commands directly; confirmed the framework corrections, **110** distinct HealthKit imports and unchanged background modes (`audio`, `fetch`, `location`, `remote-notification`).
- Direct binary counts confirm new Alo/wearable/model-defaults tokens and removed Notes literals. The ASR duplex URL occurs in both builds. These checks do not authenticate decrypted strings or prove upload execution.

## Validation and reproduction

```bash
python3 scripts/verify-october6-audit.py
python3 scripts/test-inventory-app.py
python3 scripts/inventory-app.py extracted/v9/Muse.app extracted/v9/inv-6.0-reviewed.json
shasum -a 256 -c evidence.sha256
```

The earlier verifier was made importable so its signature/page/resource logic can be reused. Its default September verification result was compared with the committed historical JSON to guard against changing the previous audit. All **8 inventory regression tests**, **64 evidence checksums**, evidence JSON parsing, Python syntax, local Markdown target checks and `git diff --check` pass. The inventory regression fixtures cover embedded PNG markers, CRC/truncation errors, invalid MP4 lengths, malformed Mach-O commands/regions, invalid fat-slice bounds and appended JPEG markers.

The report links official Android/Apple guidance for OS limits and the Sparkle maintainer's deployment preconditions. Those sources contextualize the local checks; they do not establish Muse's runtime behavior. No target app was executed, no account was used and no production traffic was captured. Native transmission, actual defaults, retail iOS plaintext authenticity, retention/deletion and live enforcement remain open.
