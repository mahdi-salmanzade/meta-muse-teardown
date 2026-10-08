# Methods, evidence and reproduction

[Overview](README.md) · [Version history](VERSIONS.md) · [Research history](RESEARCH-HISTORY.md) · [Evidence index](EVIDENCE.md)

This is a bounded client-side investigation. It combines package inspection, selected code traces, version comparisons, public-source captures and isolated tests of the older browser extension. **No native Muse app or Meta account was used in the recorded tests.**

## What each kind of evidence means

| Evidence | What it can establish | What it cannot establish by itself |
|---|---|---|
| Package hash / signature | Identity and integrity of the checked artifact or signed region | Safe behavior, absence of vulnerabilities or authenticity of unsigned/decrypted regions |
| Static code / disassembly | A selected branch, capability, constant or control exists in that sample | Production activation, exhaustive gate coverage or actual data transmission |
| Strings / imports / UI copy | A named capability, dependency or disclosure is present | Complete implementation, granted permissions or runtime use |
| Version comparison | A component, permission, byte range or selected reference changed | That every alternative path disappeared, or unchanged names mean unchanged behavior |
| Local browser execution | Behavior under the recorded synthetic fixture and local gateway | Native app behavior or production server handling |
| Public page / API capture | What that source returned at the recorded time | Legal ownership, an entire service's policy, or unseen backend behavior |

Original finder ledgers contain hypotheses and superseded interpretations. Their labels and reviewer agreement are not independent proof. Use the corrected reports alongside them.

## Platform provenance

**macOS:** Developer ID/code-signing checks and recorded notarization assessment establish package provenance. Later update-feed signature checks include a tampered-artifact negative control. An unsigned capability claim still needs its own code evidence.

**Android:** APK signatures/source stamps, matching signer checks, manifest comparisons and selected DEX disassembly support the findings. JADX reconstruction errors are decompiler errors, not app crashes. Broken branches require instruction-level verification before drawing a security conclusion.

**iOS:** third-party decrypted 8.1 and 9.1 IPAs have valid CMS signatures over checked signing metadata. Their decrypted instructions do not match signed hashes covering the original encrypted region. Matching unchanged pages and import metadata does not authenticate behavior inferred from decrypted instructions.

## Reproduce the work

Run from the repository root. App archives and extracted source are **not distributed in this repository**. Obtain the exact sample/build, compare its hash with the relevant evidence, and use the paths expected by each script. A newer download is not an equivalent baseline.

### 1. Verify the published evidence

```bash
shasum -a 256 -c evidence.sha256
```

This verifies all **76 tracked evidence files** against the manifest. It does not verify the truth of the prose or authenticate the original apps. See [EVIDENCE.md](EVIDENCE.md) for every file.

### 2. Inspect the original Mac sample

```bash
git clone https://github.com/mahdi-salmanzade/meta-muse-teardown.git
cd meta-muse-teardown
./scripts/reproduce.sh ~/Downloads/Muse-3.0.dmg
```

Requires macOS command-line tools and Python 3. The script mounts read-only, uses a temporary copy, inspects the app and cleans up. It never launches Muse. It does not regenerate every historical evidence file byte-for-byte.

### 3. Collect the original review extracts

```bash
python3 scripts/collect-review-evidence.py mac extracted/Muse.app --output /tmp/muse-mac-review
python3 scripts/collect-review-evidence.py android extracted-apk/jadx/sources evidence-android --output /tmp/muse-android-review
python3 scripts/collect-review-evidence.py ios com.facebook.hatch_8.1_und3fined.ipa extracted-ipa/Payload/HatchApp.app --output /tmp/muse-ios-review
python3 scripts/collect-review-evidence.py release --output /tmp/muse-release-review
```

The first three commands inspect local saved samples. Android requires existing JADX output; iOS uses macOS tools and records signature limitations. Only `release` fetches a public update feed, so its output reflects the time it is run. [Detailed extraction notes](reports/README.md).

### 4. Repeat the dated comparisons

| Work | Entry point | Inputs and limits |
|---|---|---|
| September release comparison | [collect-release-audit.py](scripts/collect-release-audit.py) | Saved September packages/extractions; [report setup and commands](RELEASE-AUDIT-2026-09-27.md). |
| September independent verification | [verify-september27-audit.py](scripts/verify-september27-audit.py) | CMS/page/resource and selected native/DEX checks; macOS tools and OpenSSL. [Review](TODAYS-CHANGES-AUDIT-2026-09-27.md). |
| October independent verification | [verify-october6-audit.py](scripts/verify-october6-audit.py) | Archives in `muse-v9/`, extractions in `extracted/v9/`, earlier baselines. macOS tools, Python, OpenSSL 3, Android build tools and JADX/dexlib. Paths/tool versions are recorded in the script. [Report](V9-AUDIT-2026-10-06.md#reproduce-and-next-verification). |
| App file accounting | [inventory-app.py](scripts/inventory-app.py) | Hashes, selected structural checks and byte accounting; not a malware scan. [Regression fixtures](scripts/test-inventory-app.py). |
| October 8 follow-ups | [Evidence captures](EVIDENCE.md#follow-up-investigations--8-october-2026--12-files) | Commands, offsets and public responses are in the notes. No single collector rebuilds the entire investigation. |

Inspect script paths/options before running: these research helpers assume the saved sample layout and some write their dated output files. Generate comparisons separately from published evidence when assessing a different sample.

### 5. Reproduce the older browser tests

[Offline fixtures](scripts/test-extension-boundaries.cjs) cover 14 cases with mocked browser/socket state. [Browser integration](scripts/test-extension-browser.cjs) uses Playwright/Chromium, synthetic pages and a loopback WebSocket gateway. The [September report](RELEASE-AUDIT-2026-09-27.md) records the invocation and observations.

Both concern the extension bundled in Mac 3.0/4.1. They do not exercise a native app or establish production account isolation. Mac 6.0 does not bundle that component.

## Keep future findings readable and reviewable

For each new claim, the contributor should record: **platform/build, research date, observation, method, evidence link, controls and remaining uncertainty**. The repository maintainer should review the claim against its evidence before changing the summary.

Update the platform guide and version history when the app changes; update research history when a conclusion changes. Preserve original evidence, add a new dated verification file and checksum, index it, and explain corrections in [REVIEW.md](REVIEW.md). Keep long traces in reports/evidence, not in the README. Use “latest inspected,” not an undated “latest version.”

A new native result must state the device/build, synthetic fixture, permission and account state, observed outcome and negative control. Planned tests are not results. [Next verification plan](RESEARCH-PLAN.md).
