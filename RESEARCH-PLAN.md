# Research plan: Muse on macOS, iOS and Android

[Reports](README.md) · [Review log](REVIEW.md) · [Commit audit](COMMIT-AUDIT.md) · [Evidence index](EVIDENCE.md)

**Goal:** a complete, reproducible account of what Muse can access on each platform, what it sends to Meta, when, with what consent, and what can be deleted, separating **what the code shows** from **what the app actually does**.

**Current status, 8 October 2026:** the [October build comparison](V9-AUDIT-2026-10-06.md), [independent review](TODAYS-CHANGES-AUDIT-2026-10-06.md) and [October 8 follow-ups](RESEARCH-HISTORY.md#8-october-investigate-voice-configuration-and-trust) are published. Latest inspected samples: Mac **6.0**, Android **9.0.0.23.178**, and third-party decrypted iOS **9.1.0**. Earlier versions remain comparison baselines; iOS 9.0 was listing-only. See [versions](VERSIONS.md) and [evidence](EVIDENCE.md).

**Completed:** bounded static analysis, package/version comparisons, independent checks of selected claims, public-source captures and older-extension tests (14 offline fixtures plus real isolated Chromium). The browser pause/restart/unpair findings were reproduced with synthetic data and a loopback gateway. **No logged-in native tests below have been run.** Signed iOS metadata does not authenticate decrypted instructions.

---

## Phase 1: bounded static analysis (no app execution)

The planned pass is complete, not an exhaustive security audit. iOS instruction-level control flow and its exact Health request set remain open; that line of work was stopped early. Strings, imperfect JADX reconstruction and the iOS sample’s failed integrity verification limit the conclusions. The [commit audit](COMMIT-AUDIT.md) records corrections to the initial S3–S5 summaries.

| # | Workstream | Question it answers | Platforms | Output | Status |
|---|---|---|---|---|---|
| S1 | Capability teardown | What can each build access? | all | [macOS](MACOS.md) / [Android](ANDROID.md) / [iOS](IOS.md) | done |
| S2 | **Cross-platform data matrix** | Per data type: access mechanism, on-demand vs background, backfill depth, approval gate, default, evidence | all | [Findings](CROSS-PLATFORM.md) / [detailed baseline](reports/CROSS-PLATFORM-BASELINE.md) | done (static) |
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

## Follow-up tests from the October findings

These are planned tests, not results. Start with synthetic/local fixtures where possible; production server configuration must be observed through normal use, not inferred from a forced local setting.

| # | Question | Controlled check | Evidence needed |
|---|---|---|---|
| D9 | Do the new Mac connector switches enforce denial? | Compare switch/approval/OS-grant states; revoke mid-queue with synthetic records | State screenshots, timestamps and serialization/publish outcomes |
| D10 | Which payment-key validation branches run? | Local fixture: valid/invalid key chain, flag false/true, `devExternal` false/true; invalid TLS as separate control. Never use real cards | Branch outcomes; separately record any actual server policy observed during normal test-account use |
| D11 | What starts/stops voice or wearable recording? | On available test hardware, record mic grant, session entry/exit, pairing/owner checks and sync denial using synthetic audio | Permission/UI states and synthetic payload markers; shipping availability kept separate from code presence |
| D12 | Which VM proof and enforcement policy are selected? | Record normal test-account configuration and selected proof type; independently validate supplied proof material | Authentic response capture, verification result and public-log discovery limitations |
| D13 | Which iOS background tasks actually execute? | Test permitted photo/location/audio flows while foregrounded/backgrounded; compare declarations with observed scheduling | Device/build, OS grants, task logs and outcomes; no inference from task names alone |

**Rules for Phase 2:** own test device and test account only; no attempts against Meta's servers beyond normal app use; no bypass of other users' data; captured payloads are published only with synthetic content.

## Phase 3: publication

- Update each platform report with the S2–S5 findings, and later with D1–D13 results, marking each claim **static** or **observed**.
- Keep [REVIEW.md](REVIEW.md) as the list of open and closed questions.
- The existing collector regenerates a subset of evidence, not all S3–S5 notes. The latter include manual traces and source references. `scripts/collect-commit-audit.py` regenerates the audit extracts from the local samples; public statements require separate live verification. Full automated reproduction of all evidence is still open.
- Before using broken JADX branches as a security conclusion, check the corresponding DEX/smali control flow. Verify active attestation/relay configuration and extension-token invalidation in controlled tests; these are still open beyond the completed static inventory.
