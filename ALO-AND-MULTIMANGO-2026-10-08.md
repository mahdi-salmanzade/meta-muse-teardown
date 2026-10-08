# Alo, the "Muse Gadget" wearable, and multimango.com — 8 October 2026

[Reports](README.md) · [v9 audit](V9-AUDIT-2026-10-06.md) · [Binary verification](evidence-updates/2026-10-08/04-binary-verification-alo-wearable.txt) · [Domain recon](evidence-updates/2026-10-08/01-multimango-recon.txt) · [API probes](evidence-updates/2026-10-08/02-multimango-api-probes.txt) · [Site strings](evidence-updates/2026-10-08/03-multimango-site-strings.txt)

**Finding:** the third-party decrypted iOS 9.1 sample adds Alo voice-session code and wearable-recording upload code, plus a conditional model-defaults fetch from `multimango.com`. Captured site code connects Mango to Muse: “Thank you for all your help turning Mango into Muse!” This supports a project relationship, not verified legal ownership, shipping hardware or observed user-audio transmission. Selected offsets and older-sample controls were independently rechecked on 8 October.

**Scope:** static sample analysis plus captured public-site/API responses. [Plain-language iOS guide](IOS.md) · [Methods](METHODS.md).

**Limits inherited from the v9 audit still apply.** The iOS 9.1 sample is third-party decrypted; its instruction bytes are unauthenticated. No native app was run, no account used, and no native app traffic was captured. Public-site/API requests were made and recorded. The presence of a channel is not proof that any particular user's audio traversed it. The "spyware by design" label remains an editorial privacy assessment.

## 1. Alo: live microphone audio to Meta's vLLM proxy

Verified in the 9.1 binary, absent in 8.1 ([offsets and counts](evidence-updates/2026-10-08/04-binary-verification-alo-wearable.txt)):

- Persona: `"You are Alo, a personalized AI assistant that is always on built by Meta AI."` (`0x3cb78b0`)
- Transport: `wss://shortwave.facebook.com/vllm_proxy` (`0x3cb7030`), opened from `HCHAloRealtimeTransport` on queue `com.meta.hatch.alo.ws`
- Protocol: OpenAI-Realtime-style events — `input_audio_buffer.append` carrying the microphone audio, `session.update` with `{"type":"realtime","template":"s2s"}`, `response.output_audio.delta`, `conversation.item.input_audio_transcription.*`, server-VAD `speech_started`, and a `semantic_vad_avocado` variant name — "Avocado" is Meta's [reported internal text-model codename](https://www.blockchain-council.org/ai/metas-internal-models/)
- A server-side `orchestrator.dispatch` tool: *"Always-on, server-side text-only orchestrator… access to subagents, sandboxed code execution… Dispatch is async / fire-and-forget — the orchestrator follows up via a notification."*
- The persona is loaded from on-disk files (`[AloPrompt] no persona files readable; using fallback`) and injects a `## About the person you're talking to` memory section.

8.1 already streamed dictation audio to `shortwave.facebook.com` (`/voyager/v1/asr/duplex`), so off-device audio as such is not new. **The new code describes a speech-to-speech session channel with tool use, memory injection and an async orchestrator.** Session persistence and background capture were not observed.

**Gates:** entering voice mode is server-gated (`voice_entrypoint_enabled` appears inside a server-pushed capability schema) plus a local `aloVoiceEnabled` toggle, and the OS microphone prompt still applies. That prompt — *"This allows you to talk to Muse and ask questions with your voice"* — is byte-identical to 8.1 and says nothing about an "always on" assistant, memory, or a wearable. "Always on" itself is persona copy; `UIBackgroundModes` is unchanged (`audio, fetch, location, remote-notification`) and no new background-capture capability was found.

## 2. "Muse Gadget": a BLE audio wearable whose recordings upload to Meta's VM

Verified 9.1-only code: `HCHDeviceBLEManager` (CoreBluetooth central), `HCHMicroRecordingUploader`, OTA firmware via MCUboot SMP pulled from `scontent.xx.fbcdn.net/mci_ab/uap/?ab_page=HatchFirmware…`, device-log pull (`hch_micro_device_logs`), and Wi-Fi provisioning. Recordings upload *"over the Noise gateway transport"* (`0x3cb8c00`) — an encrypted Meta distribgw/Noise channel that pre-existed for dictation; the wearable consumer of it is new. Internal lineage strings (`com.meta.stella.HCHMicroBLEManager`, `com.stellaapp.microStore`) connect it to Meta's Stella wearable project, consistent with Meta's [23 September glasses announcement](https://about.fb.com/ltam/news/2026/09/tu-agente-personal-llega-a-los-lentes-con-ia/).

**Controls present in the reviewed traces:** pairing consent with a hardware-button confirmation, a *"Verified Meta device"* badge, a stark community-device warning (*"It will be able to read and send messages, change your files, approve actions, and use your browser. This is dangerous."*), a sync-refusal path (*"Got file list but sync is not allowed"*), and a fail-closed ownership check — *"Refusing to upload recording %s: owner does not match session user — fail-closed, leaving pending."* `bluetooth-central` is absent from background modes; the state-restoration key alone does not establish ordinary BLE central-role background execution. No shipping hardware, ambient recording or actual upload was observed.

**The privacy question is who could be recorded.** If the wearable captures nearby speech, people other than the account holder may be included. Pairing and owner checks do not establish bystander consent. No bystander notification/consent mechanism was identified in the reviewed code, but recording scope, hardware indicators and actual use remain untested.

<a id="3-multimangocom-is-metas-unbranded-research-surface-for-project-mango"></a>

## 3. multimango.com: site code connects Mango to Muse

The 9.1 binary contains a conditional path to fetch Alo's model defaults from `https://www.multimango.com/api/alo/default-models` (`0x3cb6650`, with a MobileConfig fallback). The domain does not look like Meta ([recon](evidence-updates/2026-10-08/01-multimango-recon.txt)):

- Registered 2025-07-24 through GoDaddy (registrant privacy); GoDaddy nameservers
- Hosted on Vercel; Let's Encrypt certificate; no Meta branding, legal entity or contact on the public pages
- Its "Responsible Data Controller" page hides the legal entities behind authentication; the API returns `401 Authentication required`
- Public reporting describes Multimango as a gig-work AI data-annotation platform used by labor brokers ([Nodemaven review](https://nodemaven.com/blog/multimango-review/), [Steemit](https://steemit.com/ccs/@simonnwigwe/multimango-a-client-platform-for-ai-data-annotation-t7afoq))

The site's own shipped JavaScript connects the research surface to Meta's products ([verbatim strings](evidence-updates/2026-10-08/03-multimango-site-strings.txt)):

> **mangoRetirement:** "The mango research surface within Multimango has served its purpose and is being sunset. Please continue creating and debugging in Meta.ai and the Meta AI App." — "Thank you for all your help turning Mango into Muse!"

The same captured bundle describes research tooling: an Alo desktop dictation app with a data notice (stores *"the audio recording of each dictation"*, raw and cleaned transcripts, user edits, *"screenshots captured during that turn"* and session metadata; used for *"failure-mode analysis"* and *"improving our models — training and evaluating them"*; retention *"Never, 7, 14, or 30 days, or indefinitely. **The default is 7 days**"*), onboarding that says *"Grant the required permissions once. **Alo will use them in the background after setup**,"* meeting-notes capture supporting *"Laptop, phone, and **Meta glasses**,"* per-annotator quality dashboards, and a *"Live S2S bug reports"* console where reviewers inspect *"screenshots or screen recordings."*

The Muse iOS app still hardcodes this domain in the inspected 9.1 sample. Only a model-defaults fetch was found in the binary; **no user-content upload to multimango.com was observed**, and the retirement notice says the research surface is being sunset. Domain registration is anonymous, so corporate ownership is inferred from the site's own Meta/Mango/Muse strings rather than from registration records. The dictation data notice appears to address Alo desktop-app users; whether its audience is internal testers or the public, and whether any production Muse user's audio was reviewed on this platform, is not established.

### Why the unbranded domain matters

The inspected app can fetch voice-model configuration from a domain whose public pages did not clearly identify its legal operator during the capture. The site's Mango/Muse strings establish a useful attribution lead, while its research/annotation interfaces raise questions about who uses that surface. They do not prove production Muse audio reaches annotators, that the operator concealed its identity deliberately, or that no relevant disclosure exists elsewhere. The next step is to establish the operator and observe when the configuration path is used.

## 4. Verification status

| Claim | Status |
|---|---|
| Alo persona, `vllm_proxy` WebSocket, realtime-protocol events in 9.1, absent in 8.1 | **Verified** byte-exact at cited offsets, 8.1 control negative |
| Wearable BLE manager, recording upload over Noise gateway, owner fail-closed check, absent in 8.1 | **Verified** byte-exact; Noise/DGW transport itself pre-exists (correction re-verified) |
| Gates: mic prompt unchanged, server-gated voice entry, pairing consent, community-device warning, no background-capture capability delta | **Verified** from plists and strings |
| multimango.com registration/hosting facts; API 401; Meta/Mango/Muse strings in site bundle | **Verified** live on 2026-10-08 ([evidence](evidence-updates/2026-10-08/)) |
| Corporate ownership of multimango.com | **Inferred** from site's own strings; registration anonymous; could be a Meta-contracted operator |
| Any user audio or content sent to multimango.com | **Not observed**; only a model-defaults fetch is in the binary |
| Continuous/background/"always on" capture | **Not established**; "always on" is persona copy; background modes unchanged; no native runtime observation |
| iOS 9.1 sample authenticity | Unchanged: CMS metadata verifies, **decrypted instructions unauthenticated** |

Corrections to the 6 October ledger applied here: `0x3cb6820` is the WS queue label, not audio strings; 8.1 already used `shortwave.facebook.com` for dictation; "base64 PCM" is protocol inference (Alo output is Opus); the wearable upload consumes a pre-existing Noise/DGW transport.

## 5. Open questions

1. Who is the legal operator of multimango.com (the entity list is behind login), and under what contract does it serve a shipping Meta app's model defaults?
2. Did annotators on this platform review any production Muse/Alo user audio, and what were they shown? The dictation notice and S2S bug-report console establish capability and practice for the Alo desktop surface, not the Muse mobile user base.
3. When is the multimango fetch taken versus the MobileConfig fallback, and is the fetch authenticated/pinned? A Vercel-hosted config plane is a supply-chain surface worth runtime testing.
4. What does the wearable upload contain beyond audio (the device-log pull path), and where do "community devices" come from?
5. How is this configuration dependency maintained after the research surface sunsets? The notice alone does not establish that the domain will expire or change ownership.

If Meta disputes any finding, open an issue with specifics and it will be corrected.
