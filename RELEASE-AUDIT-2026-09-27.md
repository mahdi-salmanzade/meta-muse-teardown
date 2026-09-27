# Muse release audit — 27 September 2026

[Reports](README.md) · [Evidence index](EVIDENCE.md) · [Research plan](RESEARCH-PLAN.md)

**Later the same day:** [independent review of all today's changes](TODAYS-CHANGES-AUDIT-2026-09-27.md). The browser findings below reproduce; newer integrity checks and corrections to the later verdict are recorded separately. The 60-file validation count below describes this original release-audit pass, before the two subsequent evidence files.

**New Mac and Android samples are available. The strongest new findings concern the unchanged browser extension: its Pause control does not stop browsing-metadata events, pause does not survive a browser restart, and unpairing retains the last command's parameters.** These three behaviors were reproduced using the original extension in an isolated Chromium profile with synthetic pages and a loopback gateway. They are not observations of Meta receiving personal data.

This follow-up combines release provenance, version comparison, DEX instruction checks, 14 offline JavaScript tests, and a real-browser integration test. The macOS/iOS/Android native apps were not launched. No Meta account was used. The earlier reports describe the original samples; this supplement records what was checked in the newer ones.

## 1. Releases and provenance

| Platform | Previous sample | New result | Evidence strength |
|---|---|---|---|
| macOS | 3.0 / `1075746581` | **4.1 / `1077426479`**, production feed dated 25 September, 15:20:49 −0700 | Downloaded from the feed; verified Developer ID integrity, notarization assessment and Sparkle Ed25519 signature against the public key in the verified 3.0 bundle. A one-byte-modified copy fails that signature check. |
| Android | 8.0.0.21.168 / `1061301140` | **9.0.0.11.178 / `1061401140`** | Downloaded from APKPure; APK v3 signature and source stamp verify. Signing certificate matches the previous sample. SHA-256 independently matches the Uptodown listing. This is not a separately obtained Play-store trust anchor. |
| iOS | 8.1.0, unauthenticated decrypted-looking IPA | **9.0 listed on Apple's US web page**, dated 26 September 18:41:05 UTC | Directly fetched web-page version-history data. Apple's lookup API still returned 8.1. No 9.0 IPA acquired or audited, and rollout to every account/region is not established. |

New sample SHA-256s:

- Mac DMG: `7a407afc995365da2a21445a123d9609cfb2a285fa9cf859aee8430551a74561`
- Android APK: `fc4e70f48915a86094329b8b1f5941ea6eccc78d1dfee1d7a73638e7162194e3`
- Android signing certificate: `a16bbe0247a738bc8f09fef50d890dc177ec875a83a121f877329b1b89667e99`

[Acquisition metadata](evidence-updates/2026-09-27/01-release-status.json) · [Mac verification and comparison](evidence-updates/2026-09-27/02-macos-comparison.json) · [Android verification and comparison](evidence-updates/2026-09-27/03-android-comparison.json).

Sources: [Meta's production feed](https://www.facebook.com/endo/release/appcast.xml?channel=production), [Apple's listing](https://apps.apple.com/us/app/muse-from-meta/id6760173601), [Apple lookup endpoint](https://itunes.apple.com/lookup?id=6760173601&country=us), [Android mirror listing](https://com-facebook-aura.en.uptodown.com/android). Store/catalog metadata can lag or vary; downloaded-file metadata is the basis for the audited versions.

## 2. Browser extension: findings reproduced with synthetic data

**Scope:** Muse Browser Node **1.0.8**, the same 20 files in both Mac packages, all byte-for-byte identical. The findings below concern its standalone browser-node connection. Its managed-browser mode checks a `.bundled` marker and skips node connection; that mode was not tested. Availability of this exact extension in an independently distributed Chrome Web Store package was not verified.

The real-browser test used Chromium **153.0.8010.12**, an empty temporary profile, the unmodified extracted extension, a local HTTP page and a local WebSocket gateway. The gateway accepted a clearly synthetic token through the extension's internal **manual** pairing path; it is a fixture, not a substitute for testing production web pairing. External hostname resolution was disabled. No existing browser profile, account or user data was used. The profile and server were removed after the test.

| Finding | Evidence level | Observed result and limits |
|---|---|---|
| **Pause allows event metadata to continue** | Real Chromium + unit tests | A newly loaded synthetic page's full URL, including its query, and title reached the loopback gateway while `paused=true`. A fresh `tabs.list` request was rejected with `paused`. Unit tests also exercise download filename/URL events. Pause is checked in command execution, not in `events.js` or `send()`. |
| **Pause resets after restart** | Real Chromium + unit tests | Pause was present in `chrome.storage.local._cachedStatus` before closing Chromium. After reopening the same temporary profile and the extension popup, the connection reconnected with `paused=false`; `tabs.list` succeeded. The constructor initializes false and does not restore the cached pause. This proves the tested browser-restart case, not every service-worker suspension scenario. |
| **Unpair retains the most recent command parameters** | Real Chromium + unit tests | A synthetic value was actually typed into a synthetic page using `page.type`. Unpair removed `authToken`, but `_cachedStatus.lastCommand.params.value` retained that value. This is local extension storage persistence, not proof of public access or remote exfiltration. |
| **Pause does not cancel an in-flight command or its result** | Unit tests only | A pending synthetic command completed and emitted a result after pause. This may be intended command semantics; the Pause label alone does not promise cancellation. |
| **Connection changes do not isolate all old results** | Unit tests only | The request-result cache survived unpair/re-pair. Reusing a request ID replayed the previous result; separately, resolving an old pending command after re-pair sent its result to the new mock socket. The latter did not require request-ID reuse. Production account switching, server acceptance, attack reachability and actual exposure to another user remain untested. |
| **Client expiry is not an enforcement boundary** | Unit tests only | Credentials with `expiresAt=1` were loaded and passed to the mock socket constructor. Production server rejection may still enforce expiry; no expired credential was tested against Meta. |

The tests also confirm safeguards rather than treating every capability as a bypass:

- Fresh commands are blocked while paused.
- Metadata for tested blocked domains and non-web/private-control URLs is suppressed.
- Web-pairing validation rejects insecure WebSockets, foreign gateway hosts and lookalike sender origins.
- Retired `endo` credential records are discarded.
- Unpair disconnects the socket, and subsequent synthetic tab events are not sent on it.

**Implication:** in this extension, “Pause” is a command-execution switch, not a reliable collection-stop switch. The tested unpair flow stops sending but is not a complete local-data erasure operation. Recommended implementation changes are to define and enforce pause semantics on the event path, restore pause before reconnecting, clear sensitive cached command fields on unpair, and bind pending/cached results to the connection that produced them. These are recommendations, not patches applied to Meta's app.

[14-test results](evidence-updates/2026-09-27/04-extension-unit-tests.json) · [Real-browser results](evidence-updates/2026-09-27/05-extension-browser-tests.json) · [Hashed source excerpts](evidence-updates/2026-09-27/06-extension-excerpts.txt).

## 3. What changed on Android

### Network-state publishing changed, rather than disappeared

In 8.0, `NetworkStateDataSource` describes a connectivity-change callback that schedules a worker. In 9.0, the source explicitly selects **`AppOpen`** and **`TRANSIENT`** delivery. The old `network_state` worker input branches to an early return, and the manager's cancellation path still cancels the legacy job name. The source remains enabled and contains a publish path.

The disassembled 9.0 runner checks connectivity for transient delivery and returns without calling the source when disconnected. Therefore the supported statement is narrower: **this source moved from the legacy connectivity-change work path to an app-open, connection-dependent path**. It is not evidence that all network data collection stopped, that every possible trigger was audited, or that the server does not retain a received snapshot. `TRANSIENT` names a client delivery policy, not a retention guarantee.

### Approval fallbacks checked below the Java decompiler

JADX 1.5.5 reported **183 reconstruction errors** for the new APK. Rather than treating incomplete Java output as executable truth, selected classes were disassembled directly from the signed DEX files.

The reviewed bytecode preserves these important distinctions:

- `PermissionDefaultMode.Companion.fromWire()` falls back to `AUTO_ALLOW` when no wire value matches.
- `HatchNodeHitlGate.resolveConnectorBaseline()` returns `ALWAYS_ASK` for proactive sync with no cached baseline. A failed foreground fetch also resolves to `ALWAYS_ASK`.
- The `ask()` path denies proactive requests instead of prompting. This prevents a missing baseline from being interpreted as universal permission to upload.
- The reviewed worker and shared runner call the category gate when the source maps to a `NodeHitlSpec`; that does not prove every publishing path or source has the same category gate.

No live account defaults or production feature flags were measured. The older report's distinction between category checks, OS permission, source settings and server policy still applies.

### Other bounded changes

- **All 65 declared `uses-permission` entries are unchanged**, including the 19 health-data categories plus history/background access. Unchanged permissions do not establish unchanged behavior.
- New named classes describe task-specific and recipient-specific permission management. Their existence supports a new client code surface, not verified rollout or server enforcement.
- The APK still targets SDK 36, while its build metadata identifies compile SDK 37.

[Manifest/signature comparison and new-class inventory](evidence-updates/2026-09-27/03-android-comparison.json) · [Source and DEX excerpts, with hashes and code offsets](evidence-updates/2026-09-27/07-android-bytecode-excerpts.txt).

## 4. What changed on Mac beyond the extension

There are 68 changed regular files in the bundle comparison. The main executable, UI bundle, resources and several signed helper/framework binaries changed; file changes alone do not establish functionality changes.

The entitlements and privacy usage descriptions match 3.0. The selected literal local-tool-name set and extracted `autoSyncCopy` function also match. The browser extension remains identical.

New native strings mention credential-record/transport structures, native credential migration, renewed-cookie storage and rejected or incomplete cookie persistence. Other added strings describe a 4 KiB list limit so file-deletion approval cards can show every path. These identify specific areas for further testing. They do **not** prove a particular keychain design, complete credential cleanup, or enforcement of the approval-text limit.

The public [not-a-mused disclosure](https://github.com/pwardle/not-a-mused) describes a local dictation-endpoint/token-exposure issue. This pass did not execute that PoC, change Muse preferences, retrieve authentication material, or independently validate its fix. A surviving endpoint-related string is insufficient evidence of a surviving vulnerability.

## 5. Reproduce this follow-up

Keep new packages and extractions under the ignored `extracted/` tree. Preserve the original root-level `Muse-3.0.dmg` and `muse-from-meta-8-0-0-21-168.apk`, and the baseline Android JADX sources at `extracted-apk/jadx/sources/` used by the original report. All full packages and decompiled source remain excluded from Git.

1. Fetch the production feed and save it as `extracted/release-audit-2026-09-27/appcast.xml`; download its enclosure to `Muse-4.1.dmg` in that directory. Mount read-only and copy its `Muse.app` there. Extract the original 3.0 bundle to `extracted/Muse.app`. Do not launch either app.
2. Download the exact Android version via the acquisition URL in `01-release-status.json` to `Muse-android-9-candidate.apk`. Verify its version, signature and SHA-256 before treating it as the reviewed artifact. Decompile with `jadx -j 4 --no-res -d extracted/release-audit-2026-09-27/android-jadx APK_PATH`, retaining output as `jadx.log`. JADX exit code 3 occurred here because of the recorded reconstruction errors.
3. Save the direct App Store HTML and lookup JSON as `appstore.html` and `itunes-lookup.json` in that work directory. They are mutable sources; a later live fetch may differ. Published evidence preserves selected fields, source hashes and acquisition timestamps, not full store pages.
4. Disassemble the selected DEX classes using the supplied Java helper and JADX's bundled smali library:

```bash
java -cp /path/to/jadx-1.5.5-all.jar scripts/DisassembleSelected.java \
  extracted/release-audit-2026-09-27/Muse-android-9-candidate.apk \
  extracted/release-audit-2026-09-27/android-smali \
  com.facebook.aura.permissions.defaults.PermissionDefaultMode \
  com.facebook.aura.gateway.HatchNodeHitlGate \
  com.facebook.aura.gateway.AuraProactiveSyncWorker \
  com.facebook.aura.gateway.AuraProactiveSyncManager \
  com.facebook.aura.commands.network.NetworkStateDataSource \
  com.facebook.aura.nodes.core.NodeHitlCatalog \
  com.facebook.aura.nodes.datasource.DataSourcePublishPipeline \
  com.facebook.aura.nodes.datasource.ProactiveSyncRunner \
  com.facebook.aura.nodes.datasource.DataSourceContext

node scripts/test-extension-boundaries.cjs \
  extracted/release-audit-2026-09-27/Muse.app/Contents/Resources/chrome \
  > extracted/release-audit-2026-09-27/extension-tests.json

# Requires Playwright, its Chromium, and ws. Use NODE_PATH for external installs;
# MUSE_TEST_CHROMIUM can select an already installed test Chromium executable.
node scripts/test-extension-browser.cjs \
  extracted/release-audit-2026-09-27/Muse.app/Contents/Resources/chrome \
  > extracted/release-audit-2026-09-27/browser-tests.json

python3 scripts/collect-release-audit.py
shasum -a 256 -c evidence.sha256
```

The JavaScript unit results are deterministic for these inputs. Browser timestamps/tab IDs and live OS assessments can vary; compare assertions and source hashes, not incidental IDs. The evidence collector accepts tool/work/output path overrides via `--help`. Checksums establish file identity, not truth of interpretation.

Validation for this pass: all 14 unit tests pass against both extracted extension copies and produce identical results. The real-browser assertions pass. Regenerating the seven evidence files into a separate directory produces identical files. All 60 evidence checksums, JSON parsing, script syntax and local Markdown links were checked.

## 6. What remains open

The repo owner reports having a test device and throwaway account; device identity, connection and synthetic-only service setup were not yet supplied for this pass. No logged-in native test was performed. Next live tests are fresh-account defaults, deny/revoke behavior, synthetic notification/health/photo payloads, and reconnect/queue behavior on that identified device. Do not substitute a personal profile or existing logged-in device.

Also open: an authenticated iOS 9.0 sample, production extension pairing and expiry/revocation, account-bound result handling, deployed Confidential VM enforcement, actual server-side retention and deletion, and independent verification of vendor/researcher patch claims. No cross-user leak, server exploit, or universal protection failure is claimed here.
