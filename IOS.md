# iOS: photo sync, health/location and new audio paths

[Overview](README.md) · [Versions](VERSIONS.md) · [macOS](MACOS.md) · [Android](ANDROID.md) · [Evidence](EVIDENCE.md)

**Latest inspected: 9.1.0 / `1080826056`.** Bundle: `com.facebook.hatch`. Research through 8 October 2026.

**Evidence limit:** both inspected IPAs are third-party decrypted copies. Apple CMS signatures and checked metadata verify, but the decrypted instruction bytes cannot be authenticated against signatures covering the original encrypted bytes. Code-path findings below describe these samples, not an authenticated retail execution. No native uploads were captured.

## What changed by version

| Version | What we inspected | What changed / what it establishes |
|---|---|---|
| **8.1.0 / `1074192126`** | Decrypted IPA; metadata, imports, strings and selected paths | Photo-sync controls, Health/location/HomeKit capabilities and user-created Shortcuts forwarding; original Notes-export literals. |
| **9.0** | Public listing only, checked 27 September | Store/lookup discrepancy recorded. **No code acquired or audited.** |
| **9.1.0 / `1080826056`** | Decrypted IPA compared with 8.1 | New Alo voice and wearable-recording code; conditional model-defaults URL; identified Notes-export literals removed. |

Sources: [8.1 detail](reports/IOS-8.1.md), [listing check](RELEASE-AUDIT-2026-09-27.md), [9.1 audit](V9-AUDIT-2026-10-06.md#ios-910--decrypted-sample).

## Problems and controls

### Photo sync has persistent settings as well as temporary pause

The copy describes an override for full-library sync. In 8.1, the traced `photo.sync` handler sets `cameraRollSyncEnabled = true`; the equivalent 9.1 setter was **not independently retraced**. Pausing/cancelling a run and disabling ongoing sync are different operations. Photos authorization remains necessary. A background task identifier is not proof of periodic execution: the declared modes omit `processing`. [Original photo/control detail](reports/IOS-8.1.md) · [9.1 qualifications](V9-AUDIT-2026-10-06.md#continuing-concerns-and-limits).

### Health and location are broad capabilities, not measured collection

The samples import **110 distinct HealthKit type identifiers** and contain background-delivery/raw-sample-sync indicators. That count is not 110 grants, reads or uploads. The exact requested Health set needs permission-sheet and call-boundary observation. Significant-change location and geofence paths require relevant OS authorization; HomeKit control code also depends on grants. [Original evidence](evidence-ios/11-health-import-count.txt) · [9.1 limits](V9-AUDIT-2026-10-06.md#continuing-concerns-and-limits).

### Message forwarding relies on user-created Shortcuts

iMessage and Mail forwarding are described through revocable Shortcuts automations. A historical Messages database reader was not established. The identifiable Notes-export strings disappear in 9.1; that does not rule out every alternative Notes or Shortcut path. Disconnecting does not itself delete previously shared messages, according to the app's copy. [Forwarding and retention evidence](evidence-ios/15-consent-retention-ios.txt).

### Alo adds a new voice path

9.1 adds `wss://shortwave.facebook.com/vllm_proxy`, `input_audio_buffer.append` and Alo persona/session references. The older ASR socket already existed in 8.1, so off-device audio as a whole is not new. Voice-mode controls and the microphone permission matter. Persona text saying “always on” is not proof of continuous capture. [Audio comparison](ALO-AND-MULTIMANGO-2026-10-08.md).

### Wearable-recording code raises a bystander-consent question

`HCHDeviceBLEManager`, `HCHMicroRecordingUploader` and “Muse Gadget” appear in 9.1. The reviewed traces include pairing consent, hardware confirmation, sync checks and owner-mismatch rejection. This supports a capability lead, not confirmed shipping hardware, ambient capture or observed uploads. The question for device testing is how recording and consent work for everyone nearby. [Wearable investigation and offsets](ALO-AND-MULTIMANGO-2026-10-08.md).

### Model configuration and VM trust deserve further verification

The conditional model-defaults fetch points to `www.multimango.com/api/alo/default-models`, with a MobileConfig fallback. Captured site code links Mango to Muse; the legal operator is not established, and no user-content upload to that domain was observed. Newer code removes Sigstore/Rekor proof support while retaining Plexi auditor signatures. The payment-validation configuration cannot be resolved from iOS strings alone. [Domain investigation](ALO-AND-MULTIMANGO-2026-10-08.md) · [Payment/VM investigation](PAYMENT-AND-TRANSPARENCY-2026-10-08.md).

## What we did and what remains

Verified CMS-to-CodeDirectory bindings and selected page/resource hashes, compared imports and direct framework load commands, checked new strings at recorded offsets against the older sample, and reviewed consent copy. Matching unchanged regions cannot authenticate the decrypted regions. [Methods](METHODS.md).

Still needed: authenticated retail code, observed Health request sets, photo pause/revocation behavior, native audio traffic, wearable availability/ownership enforcement and actual server policy. [Device test plan](RESEARCH-PLAN.md).

<a id="1-provenance-apple-signed-original-decrypted-by-a-third-party"></a><a id="1-provenance-consistent-with-a-decrypted-app-store-package-not-fully-authenticated"></a><a id="1-provenance-signed-metadata-unauthenticated-decrypted-code"></a><a id="10-reproduce-the-added-ios-evidence"></a><a id="2-agent-commands-and-approval-evidence"></a><a id="3-background-sync-and-remote-wakeups"></a><a id="4-photos-one-photosync-call-turns-on-ongoing-camera-roll-sync"></a><a id="5-health-110-imported-type-identifiers-not-110-proven-uploads"></a><a id="6-location-and-homekit"></a><a id="7-imessage-mail-and-notes-through-user-created-shortcuts"></a><a id="8-shared-containers-browser-sharing-and-debug-surfaces"></a><a id="9-reduce-access-or-remove-it"></a><a id="conclusion"></a><a id="muse-for-ios-comfacebookhatch-810"></a><a id="retention-wording-in-the-app"></a>

Earlier detailed sections and evidence tables are preserved in the [previous report](reports/IOS-8.1.md).
