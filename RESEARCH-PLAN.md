# Research plan: Muse on macOS, iOS and Android

[Reports](README.md) · [Review log](REVIEW.md) · [Commit audit](COMMIT-AUDIT.md) · [Evidence index](EVIDENCE.md)

**Goal:** a complete, reproducible account of what Muse can access on each platform, what it sends to Meta, when, with what consent, and what can be deleted, separating **what the code shows** from **what the app actually does**.

**Latest claim review:** [27 September independent audit](TODAYS-CHANGES-AUDIT-2026-09-27.md) reproduces the browser findings and selected integrity checks, and corrects overstatements in the later verdict. Signed iOS metadata does not authenticate decrypted instructions. Add the missing iOS `processing` mode and deployment-specific Sparkle update conditions to future runtime checks; neither has been tested live.

**Samples:** macOS 3.0 and 4.1 (`com.meta.endo`), Android 8.0.0.21.168 and 9.0.0.11.178 (`com.facebook.aura`), unverified iOS 8.1.0 (`com.facebook.hatch`). iOS 9.0 is listed but not acquired. Hashes in [EVIDENCE.md](EVIDENCE.md).

**Completed 27 September:** [Release and boundary audit](RELEASE-AUDIT-2026-09-27.md): verified newer Mac/Android packages, compared bundle and permission changes, checked selected Android branches in DEX disassembly, and exercised the original extension with 14 offline tests plus real isolated Chromium. Pause, restart and unpair persistence findings are reproduced with synthetic data and a loopback gateway. These do not complete logged-in native tests D1–D8.

---

## Phase 1: bounded static analysis (no app execution)

The planned pass is complete, not an exhaustive security audit. iOS instruction-level control flow and its exact Health request set remain open; that line of work was stopped early. Strings, imperfect JADX reconstruction and the iOS sample’s failed integrity verification limit the conclusions. The [commit audit](COMMIT-AUDIT.md) records corrections to the initial S3–S5 summaries.

| # | Workstream | Question it answers | Platforms | Output | Status |
|---|---|---|---|---|---|
| S1 | Capability teardown | What can each build access? | all | README / ANDROID / IOS | done |
| S2 | **Cross-platform data matrix** | Per data type: access mechanism, on-demand vs background, backfill depth, approval gate, default, evidence | all | [CROSS-PLATFORM.md](CROSS-PLATFORM.md) | done (static) |
| S3 | **Android & browser boundaries** | Does every background publish path reach the approval gate? Is the exported phone-ID provider caller-checked? Pairing-token storage, expiry, revocation | Android, macOS extension | `evidence-android/12-13`, `evidence/14` | done |
| S4 | **Consent, defaults & retention copy** | What do the apps *tell* users about defaults, sharing and deletion, and how does that compare with Meta's public statements? | all (UI strings only) | `evidence*/15-*` | done |
| S5 | **Network & protocol map** | Hosts, RPC/method names, transport (WSS, OHTTP), which calls carry user data; third-party SDK inventory | all | `evidence*/16-network-*` | done |

## Phase 2: dynamic testing (needs a throwaway Meta account)

Use an identified **test Android device/emulator**, spare Mac/VM or test iPhone, with a **throwaway Meta account** created by the repo owner and **synthetic data only**: fake SMS, contacts, calendar, notifications, photos and health samples. Instrumentation-dependent tests may need a rooted emulator. The owner confirms a test device and throwaway account are available; device identity, connection and synthetic-only linked services remain to be confirmed. No logged-in native tests have been run. Do not use a personal device or account.

| # | Test | Method | Answers |
|---|---|---|---|
| D1 | **Fresh-account defaults** | Install, log in, record every consent screen and the initial state of every sync switch | Are auto-sync / notification / health switches on by default? |
| D2 | **Consent enforcement** | For each category: deny → generate new synthetic data → watch traffic. Then allow → deny again | Does "deny" actually stop collection and upload? |
| D3 | **Upload contents** | Capture the test device’s traffic and instrument its own serialization/encryption boundary for `client.data_source.publish` / command results. A TLS proxy alone cannot decode inner Noise encryption; correlate synthetic markers and publish outcomes | Exactly which fields leave the device: bodies, sender, attachments, GPS, raw health samples |
| D4 | **Backfill depth** | Seed data dated 1 day / 30 days / 1 year / 5 years back; trigger connect | How much history is pulled on first connect |
| D5 | **Revocation & queues** | Revoke OS permission / disconnect connector mid-upload | Are queued uploads cancelled? |
| D6 | **Retention & deletion** | Export a baseline first using a verified available export flow. Test disconnect, forwarding-off, message deletion, memory deletion and reset separately; inspect/export while access remains. Account deletion last, after preserving results | Visible local/agent/export persistence; client tests cannot prove deletion from backups or trained models |
| D7 | **iOS Health request set** | On a fresh test authorization state, record the Health permission sheet and, where feasible, the requested type set at the app call boundary | Types requested by the tested flow; imports and permission-sheet labels alone do not prove every possible request |
| D8 | **Notification scope** | Post synthetic notifications from several apps, incl. an OTP-style message on Android 14 vs 15+ | Which notifications are published, and whether OTPs are redacted |

**Rules for Phase 2:** own test device and test account only; no attempts against Meta's servers beyond normal app use; no bypass of other users' data; captured payloads are published only with synthetic content.

## Phase 3: publication

- Update each platform report with the S2–S5 findings, and later with D1–D8 results, marking each claim **static** or **observed**.
- Keep [REVIEW.md](REVIEW.md) as the list of open and closed questions.
- The existing collector regenerates a subset of evidence, not all S3–S5 notes. The latter include manual traces and source references. `scripts/collect-commit-audit.py` regenerates the audit extracts from the local samples; public statements require separate live verification. Full automated reproduction of all evidence is still open.
- Before using broken JADX branches as a security conclusion, check the corresponding DEX/smali control flow. Verify active attestation/relay configuration and extension-token invalidation in controlled tests; these are still open beyond the completed static inventory.
