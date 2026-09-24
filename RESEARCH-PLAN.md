# Research plan: Muse on macOS, iOS and Android

[Reports](README.md) · [Review log](REVIEW.md) · [Evidence index](EVIDENCE.md)

**Goal:** a complete, reproducible account of what Muse can access on each platform, what it sends to Meta, when, with what consent, and what can be deleted, separating **what the code shows** from **what the app actually does**.

**Samples:** macOS 3.0 (`com.meta.endo`), Android 8.0.0.21.168 (`com.facebook.aura`), iOS 8.1.0 (`com.facebook.hatch`). Hashes in [EVIDENCE.md](EVIDENCE.md).

---

## Phase 1: static analysis (no app execution)

| # | Workstream | Question it answers | Platforms | Output | Status |
|---|---|---|---|---|---|
| S1 | Capability teardown | What can each build access? | all | README / ANDROID / IOS | done |
| S2 | **Cross-platform data matrix** | Per data type: access mechanism, on-demand vs background, backfill depth, approval gate, default, evidence | all | [CROSS-PLATFORM.md](CROSS-PLATFORM.md) | in progress |
| S3 | **Android & browser boundaries** | Does every background publish path reach the approval gate? Is the exported phone-ID provider caller-checked? Pairing-token storage, expiry, revocation | Android, macOS extension | `evidence-android/12-13`, `evidence/14` | in progress |
| S4 | **Consent, defaults & retention copy** | What do the apps *tell* users about defaults, sharing and deletion, and how does that compare with Meta's public statements? | all (UI strings only) | `evidence*/15-consent-retention-*` | in progress |
| S5 | **Network & protocol map** | Hosts, RPC/method names, transport (WSS, OHTTP), which calls carry user data; third-party SDK inventory | all | `evidence*/16-network-*` | in progress |

## Phase 2: dynamic testing (needs a throwaway Meta account)

Runs on a **rooted Android emulator** (and later a spare Mac/VM and a test iPhone), with a **throwaway Meta account** created by the repo owner and **synthetic data only**: fake SMS, contacts, calendar, notifications, photos and health samples. It never runs on a personal device or account.

| # | Test | Method | Answers |
|---|---|---|---|
| D1 | **Fresh-account defaults** | Install, log in, record every consent screen and the initial state of every sync switch | Are auto-sync / notification / health switches on by default? |
| D2 | **Consent enforcement** | For each category: deny → generate new synthetic data → watch traffic. Then allow → deny again | Does "deny" actually stop collection and upload? |
| D3 | **Upload contents** | Intercept the device's own traffic to Meta via a local proxy; decode `client.data_source.publish` / `node.invoke` payloads | Exactly which fields leave the device: bodies, sender, attachments, GPS, raw health samples |
| D4 | **Backfill depth** | Seed data dated 1 day / 30 days / 1 year / 5 years back; trigger connect | How much history is pulled on first connect |
| D5 | **Revocation & queues** | Revoke OS permission / disconnect connector mid-upload | Are queued uploads cancelled? |
| D6 | **Retention & deletion** | Disconnect connector, disable forwarding, delete conversation, delete account; then request a data download (Accounts Center) | What survives locally vs in Meta's cloud |
| D7 | **iOS Health request set** | Trigger Health connect and screenshot the system permission sheet | The exact HealthKit types requested (vs 110 imported identifiers) |
| D8 | **Notification scope** | Post synthetic notifications from several apps, incl. an OTP-style message on Android 14 vs 15+ | Which notifications are published, and whether OTPs are redacted |

**Rules for Phase 2:** own test device and test account only; no attempts against Meta's servers beyond normal app use; no bypass of other users' data; captured payloads are published only with synthetic content.

## Phase 3: publication

- Update each platform report with the S2–S5 findings, and later with D1–D8 results, marking each claim **static** or **observed**.
- Keep [REVIEW.md](REVIEW.md) as the list of open and closed questions.
- Every evidence file is regenerable from the samples with the scripts in [`scripts/`](scripts/).
