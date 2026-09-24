# Audit of the three static-research commits

Reviewed on 2026-09-24: `ab6f6c9`, `36f0c2b`, `9b0d5a3`, against base `df2de85`.

**The central static findings have supporting evidence, but the summaries contained material overstatements.** This revision corrects them in the reports and evidence notes. It is a bounded source/claim review, not a completed security assessment or an observation of uploads.

## Corrections, ordered by impact

| Finding | What was wrong | Corrected conclusion |
|---|---|---|
| Android approval coverage | “No approval” conflated one local category gate with every consent/control layer; geofence creation was said to require an approved command | Six source IDs map to `NodeHitlCatalog`. Reviewed location, network and battery paths lack that category check. `geofence.set` **also** maps to no command spec; it requests missing Android location grants. Source settings, OS grants, session state and remote policy remain separate. Wi-Fi SSID/BSSID are nulled without fine-location access or when scrubbed. |
| Android defaults | “If the server sends nothing, allow” collapsed two different states; “Meta decides” omitted the user-editable setting | With no per-category override, a parsed response whose field is omitted/unrecognized becomes `AUTO_ALLOW`. **No cached response instead denies proactive reads.** Saved allow/deny/ask modes take precedence; the settings UI writes the server-returned preference. Production values are untested. |
| Backfill limits | `1 MiB × 256 = 64 MiB` is wrong, and the purported maximum was not enforced | A 1 MiB page-sizing target can be exceeded by a single item. Crossing 256 chunks or 64 MiB logs a warning and **continues**. A separate 4 MiB wire-size check rejects oversized frames. This is not proof of unlimited history: source/date/page controls still apply. |
| Deletion | “May stay in memory” became “doesn't delete memory”; missing terms in reset copy were treated as exclusion | The app warns of possible persistence. “Including” introduces a non-exhaustive reset list. Disconnect retaining prior data is supported by copy; reset failure, backup survival and training retention have not been demonstrated. |
| iOS attestation | Embedded staging trust data became “checks the VM against a staging server” | The binary contains `rekor.sigstage.dev`, verifier classes and configuration gates. Active root selection, attestation enforcement and server contact are unverified; Sigstore bundle checks can be offline. The 143 bundled CA roots also do not establish which trust store each connection uses. |
| OHTTP | “Anonymous VM leasing only” contradicted the network notes' own GraphQL findings | Lease paths are identified, and shared mobile stacks contain GraphQL OHTTP support. Which requests actually use a relay remains unknown. Account credentials do not by themselves prove relay absence. |
| Extension revocation | No explicit revoke request became a claim that disconnect cannot invalidate a token | Local unpair clears credential keys and closes the socket. There is no client TTL check or explicit revoke request in that path. The server may still invalidate the token; continued validity of a copied token needs testing. |
| Training and approvals | Client fallbacks became production observations; health “may use” became categorical use; public tool-call training disclosure was understated | Preserve the client defaults and connector disclosure, but distinguish them from live state or actual training ingestion. The public research description includes tool calls. Unprompted reads fit its stated approval model. |

The phone-ID correction is supported: the provider checks the Binder caller identity and the receiver checks the creator of an `auth` PendingIntent against a signing-certificate allow-list. This is stronger than manifest-only protection, but not proof against every bypass. Only Muse's own signing hash was independently attributed; broken decompiler branches and possible delegated PendingIntents remain caveats.

## Evidence checked

- Android source: category/command catalog and enum ordinals, geofence permission requests, Wi-Fi reader, permission settings cache/fetch/update, proactive gate, backfill emitter, attribution and phone-ID paths. The network-security XML was independently decoded from the APK: 18 pins, domain-specific restrictions and a cleartext-permitted base config are present. Missing pins in that XML do not establish missing native-stack verification or actual cleartext uploads.
- macOS extension: credential storage, expiry references, unpair/close behavior, reconnect/pause and cached-command handling. UI fallback and consent claims were compared with the existing bounded web-bundle extracts.
- iOS: raw binary matches for staging/production Rekor names, verifier names and GraphQL OHTTP support; bundled CA count. This sample's signature verification already failed: the audit does not authenticate it or turn strings into executable-path proof.
- Both live public posts were read: [Meta's launch announcement](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/) and [security/research description](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse). The corrected [comparison](evidence/15-public-statements-vs-app.txt) preserves the distinction between app disclosures, vendor statements and observations.

New [primary excerpts](evidence/17-commit-audit.txt) include source-file SHA-256s and line numbers. Rebuild them from the local extractions:

```bash
python3 scripts/collect-commit-audit.py > /tmp/muse-commit-audit.txt
cmp /tmp/muse-commit-audit.txt evidence/17-commit-audit.txt
shasum -a 256 -c evidence.sha256
```

Validation: the new extractor reproduced its committed output byte-for-byte; all 53 evidence checksums passed; all 206 local Markdown links/heading anchors resolved; `git diff --check` passed.

The existing evidence collectors do **not** regenerate every manual S3–S5 note. The research plan now says so. A valid checksum proves file identity, not that an interpretation is correct.

## Still open

The completed static inventory leaves instruction-level checks of ambiguous JADX/iOS paths and the live tests outstanding. In particular, measure initial settings, deny/revoke transitions, synthetic payloads, extension token invalidation, active attestation/relay configuration and the iOS Health request set. For encrypted gateway payloads, a TLS proxy alone is insufficient because Noise adds another encryption layer. Export before account deletion; distinguish visible persistence from unobservable backend backup/model erasure.

No app was launched, no account was used, and no D1–D8 result is claimed. `REVIEW.md` and the local `video/` directory were left untouched. Two separate video-related commits (`e6970ff`, `e92f773`) arrived during this review; they are outside the three research commits audited here. Their narration has not been verified against these corrections.
