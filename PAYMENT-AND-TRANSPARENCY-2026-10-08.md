# Payment-key trust and CVM transparency — 8 October 2026

[Reports](README.md) · [Alo & multimango](ALO-AND-MULTIMANGO-2026-10-08.md) · [v9 audit](V9-AUDIT-2026-10-06.md) · [PTT flag verification](evidence-updates/2026-10-08/07-cert-skip-flag-verification.txt) · [Transparency verification](evidence-updates/2026-10-08/06-attestation-transparency-verification.txt) · [API inventories](evidence-updates/2026-10-08/05-api-inventory-macos.txt)

Two follow-up investigations from the 8 October endpoint sweep, both taken through the repo's standard adversarial verification. One headline candidate was **refuted in its strong form** and is published here in corrected form; the other **survived with a sharper finding than the original lead**. As elsewhere: static analysis, no app executed, no production traffic captured, iOS 9.1 decrypted code unauthenticated.

## 1. The PTT payment-key validation switch

**What ships.** macOS 6.0 (and 3.0 before it) ships a server-deliverable MetaConfig boolean `hatch_web:ptt_skip_certs_verification_by_payment_env` (declared in `metaconfig.json`, default **false**, present in the registered `client_mappings_default` whitelist — so, unlike the auto-sync flag from the 27 September audit, Meta's server **can** deliver this one). Android ships the exact analog (`AuraFBPayGatingProvider.skipCertsVerification`, with a `ptt_encryption_key_validation_in_skipped` telemetry field), and iOS ships the same `shouldSkipCertVerification` machinery.

**What it actually does — not TLS.** PTT is the Platform Trust Token flow in Meta Pay checkout. Before the app encrypts a card number (PAN/CVV via ECDH-ES+A256GCM), it fetches an E2EE encryption key from `/api/ptt/encryption-key` and validates that key's certificate chain against a hard-coded **"Facebook Payments Root CA"** (pkijs `CertificateChainValidationEngine`). The flag skips *that* check. TLS to the API host is never touched — the original "skips certificate verification in payments" framing would have been wrong, and this report replaces it.

```js
t = useMcBool(`hatch_web:ptt_skip_certs_verification_by_payment_env`, false);
!t && !r2.devExternal && (await verifyTrustChain(r2.trustChain) || zi(`Invalid trust chain`));
```

**Why it still matters.** The chain check is defense-in-depth against **key substitution**: if the delivered encryption key isn't anchored to Meta's payments root, a middlebox or compromised config plane could swap in its own key and decrypt card data. Three facts sharpen this:

1. **Checkout runs LIVE by default** (`container_mode` default `"LIVE"`); the consumer sits on the real save-card → `/api/wallet/cards` path.
2. **There is no client-side production guard.** No environment enum or comparison exists anywhere in the client; the boolean is used raw. The "by_payment_env" naming reflects intended server-side targeting only.
3. **A second bypass needs no flag at all.** The server's own `/api/ptt/encryption-key` response can carry `devExternal`, which disables the same validation **regardless of the flag's value** — a server-only switch for the same check.

Whether any production user ever receives `true`, or a `devExternal` key response, cannot be determined statically. The finding is: the validation that protects card-data encryption keys is optional, server-controlled from two directions, and unguarded on the client — in the live checkout path of a consumer app. **Runtime test plan** (flag forced true with a self-signed chain; `devExternal:true` with flag false; invalid TLS as a control) is in [07-cert-skip-flag-verification.txt](evidence-updates/2026-10-08/07-cert-skip-flag-verification.txt). Android's decompiled fail-path is marked "decompiled incorrectly", so its hard-fail behavior when the flag is false is unconfirmed; iOS 9.1's MobileConfig wiring is unresolvable by strings alone.

## 2. CVM attestation transparency: what v9 actually changed

**Original lead (rejected):** "Meta replaced public Sigstore/Rekor transparency with a private Cloudflare system, ending public auditability." Verification **refuted** the framing while confirming a real, narrower change.

**Confirmed:**
- v9 (Android 9.0.0.23.178, iOS 9.1) deletes the entire Sigstore/Rekor verifier — sigstore 155→0, rekor 68→0, fulcio 8→0 string counts — and gains the literal string **"Sigstore transparency proofs are no longer supported."** Cloudflare Plexi-auditor signatures are now the sole supported transparency proof for the VM image manifest (`prod.hatch_image`) and the AMD VCEK revocation list (`prod.pc.revocation_list`).
- The client no longer checks a Merkle inclusion proof itself; it verifies only the auditor's signature.

**Refuted / qualified:**
- **Plexi pre-existed.** The full verifier and Cloudflare's pinned keys already shipped in Android 8.0, iOS 8.1 and macOS 4.1, which accepted both proof types under policy. macOS never had Rekor at all. v9 removed a redundant path, not the only path.
- **Plexi is not private.** It is Cloudflare's open-source auditor; the app pins five Ed25519 keys, two byte-identical to the keys Cloudflare publicly advertises at `plexi.key-transparency.cloudflare.com/info`. The auditor's `/namespaces` endpoint lists 115 Meta namespaces, including both of the above; we fetched the epoch-1 audit signature for `prod.pc.revocation_list` and **verified it locally against the app's pinned key** ([captures](evidence-updates/2026-10-08/plexi-info.json), [namespaces](evidence-updates/2026-10-08/plexi-namespaces.json), [audit](evidence-updates/2026-10-08/plexi-audit1.json)).
- **The removed Rekor path was pinned to Sigstore's staging instance** (sigstage.dev; no `rekor.sigstore.dev` TrustedRoot in either binary), so whether it was ever production-active is doubtful.

**The legitimate residual concerns:**
1. **Verification depth regressed:** the client trusts the auditor's signature where it previously could check log inclusion itself.
2. **No log directory:** Meta publishes no directory for its CVM namespaces, so third parties can verify auditor signatures but cannot enumerate *what was logged*. Meta's own engineering post ("How Advanced Browsing Protection Works in Messenger", engineering.fb.com, 2026-03-09) describes the same xplat CVM attestation stack with the witness-signature model and acknowledges researcher-facing artifacts are not yet released — *"We aim to provide a platform for hosting these artifacts in the near future."*
3. Whether v8 production policy ever accepted Sigstore proofs at all is server-side and statically unresolvable; if not, v9 is dead-code cleanup rather than a behavioral swap.

**Bottom line:** the accurate story is not "Meta went dark" — it is "Meta consolidated CVM transparency onto a single external auditor and has not yet delivered the public log directory and researcher artifacts it promised in March 2026." That is a deadline to hold them to, not a smoking gun.

## Verification ledger

| Claim | Status |
|---|---|
| PTT flag declared, whitelisted/deliverable, default false, since macOS 3.0 | **Verified** |
| Sole consumer is web-bundle Meta Pay checkout; native binary untouched; TLS unaffected | **Verified** |
| Checkout LIVE by default; no client-side env guard; `devExternal` server-side bypass | **Verified** from bundle code |
| Same design on Android and iOS | **Verified** (Android fail-path decompilation unconfirmed) |
| Sigstore/Rekor removed in v9; "no longer supported" string added | **Verified**, both platforms |
| Plexi pre-existed in v8/4.1; Plexi is public; audit signature independently verified | **Verified**, with live captures |
| Any production account receiving flag=true or devExternal keys | **Unknown** — runtime test needed |
| v8 production policy re Sigstore proofs | **Unresolvable statically** |

If Meta disputes any finding, open an issue with specifics and it will be corrected.
