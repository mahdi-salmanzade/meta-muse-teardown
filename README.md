![Muse privacy concern — independent teardown](assets/muse-platforms.png)

# Muse by Meta: iOS, macOS and Android privacy teardown

[**iOS**](IOS.md) · [**macOS**](#1-is-this-really-metas-app) · [**Android**](ANDROID.md) · [**All evidence**](EVIDENCE.md) · [**Review updates**](REVIEW.md)

> The internet is the 'greatest spying machine the world has ever seen' and is not a technology that necessarily favours the freedom of speech.
>
> — Julian Assange’s remarks, as summarized by [The Guardian, 15 March 2011](https://www.theguardian.com/media/2011/mar/15/web-spying-machine-julian-assange). This full sentence is the article’s summary, not a verbatim sentence from his speech.

A static teardown of **Muse 3.0 for macOS** (`com.meta.endo`), plus Android and iOS samples. Meta uses **Hatch** internally; the Mac binary also contains **Endo** names.

**The privacy issue is the breadth of access:** the Mac build contains tools for iMessage, WhatsApp, Mail, Notes, contacts, calendars, files, screen capture and computer control, plus background-sync machinery and a powerful bundled Chrome extension. Enabling a connector can expose private information to a cloud agent; some connectors support ongoing uploads.

**This report establishes shipped capabilities, not what a particular user's account uploaded.** OS permissions, connector settings, approval rules, feature flags and platform restrictions affect what actually runs. No Muse app was launched, no account was connected and no network traffic from the apps was captured. Strings and decompiled code do not establish successful execution or server-side enforcement.

### Platforms covered

| Platform | Inspected build | Report / evidence strength |
|---|---|---|
| macOS | 3.0, build `1075746581` | This page; Meta Developer ID signature verifies. Production update feed still lists this build on 2026-09-24. |
| Android | 8.0.0.21.168 (`com.facebook.aura`) | [ANDROID.md](ANDROID.md): verified APK signature/source stamp; SMS, calls, notifications, location and **19 health-data category permissions**, plus history/background permissions. |
| iOS | 8.1.0, build `1074192126` (`com.facebook.hatch`) | [IOS.md](IOS.md): **modified/decrypted-looking IPA with invalid signature**; sample-specific findings, not authenticated retail-code claims. |

### What changed in this review — 2026-09-24

- Added the iOS sample: HomeKit controls and geofence automation, HealthKit background-delivery entitlement, camera-roll sync controls and user-created Shortcuts message forwarding.
- Corrected Android's health-permission count, missing calendar backfill, notification approval gates and the unsupported claim that OTP protection is absent everywhere.
- Restored the Mac email consent copy's distinction between metadata and message bodies; removed unsupported claims about entire-library uploads and server-controlled sync defaults.
- Added current release checks and Meta's public statements about training, advertising, credential isolation and Confidential VM below. See [REVIEW.md](REVIEW.md) for the correction log and remaining unknowns.

Evidence excerpts, metadata, research scripts and the supplied banner artwork are tracked. The DMG/APK/IPA and extracted app code are excluded from Git. See [reproduction](#11-reproduce-it-yourself) for the scope of each script.

---

## Contents

1. [Is this really Meta's app?](#1-is-this-really-metas-app)
2. [Architecture: your Mac as a node for a Meta VM](#2-architecture-your-mac-as-a-node-for-a-meta-vm)
3. [What it can read](#3-what-it-can-read)
4. [What it uploads in the background](#4-what-it-uploads-in-the-background)
5. [Full computer control](#5-full-computer-control)
6. [The Chrome extension: broad debugger access](#6-the-chrome-extension-broad-debugger-access)
7. [`stealth.min.js`: a bot-detection evasion kit](#7-stealthminjs-a-bot-detection-evasion-kit)
8. [Is Muse spyware?](#8-is-muse-spyware)
9. [Meta's track record](#metas-track-record)
10. [If you already installed it](#10-if-you-already-installed-it)
11. [Reproduce it yourself](#11-reproduce-it-yourself)
12. [Current public disclosures and release status](#12-current-public-disclosures-and-release-status)

---

## 1. Is this really Meta's app?

The inspected Mac app carries Meta’s Developer ID signature and passes `codesign --verify --deep --strict`. Its recorded Gatekeeper assessment is accepted/notarized. This establishes provenance and integrity, not that the software is risk-free ([`evidence/01-signature.txt`](evidence/01-signature.txt)).

| Field | Value |
|---|---|
| DMG sha256 | `3818f35b89580d857f412977f6d8f5d409dbc3112da3e7119ea254d518010de4` |
| Bundle ID | `com.meta.endo` |
| Version | 3.0 (build `1075746581`), release channel `production` |
| Signed by | `Developer ID Application: Meta Platforms, Inc. (V9WTTPBFK9)` |
| Gatekeeper | `accepted`, `source=Notarized Developer ID` |
| Provisioning profile | "Endo Hatch MacOS Developer ID Application", Team "Meta Platforms, Inc." |
| Update feed | `https://www.facebook.com/endo/release/appcast.xml?channel=production` (Sparkle) |
| Source paths present in binary | `fbobjc/Apps/Internal/Endo/Sources/...` |

It is **not App-Sandboxed**: there is no `com.apple.security.app-sandbox` entitlement ([`evidence/02-entitlements.txt`](evidence/02-entitlements.txt)). It is not restricted to an App Sandbox container. Unix permissions, macOS privacy controls and other OS protections still apply.

Declared entitlements (these are not user permission grants):

```
com.apple.security.automation.apple-events      = true   (script other apps)
com.apple.security.device.audio-input           = true   (microphone)
com.apple.security.device.camera                = true
com.apple.security.personal-information.addressbook
com.apple.security.personal-information.calendars
com.apple.security.personal-information.photos-library
com.apple.security.personal-information.reminders
```

The `Info.plist` also asks for Desktop, Documents, Downloads, network volumes, removable volumes, location, speech recognition and Apple Events ([`evidence/03-info-plist.txt`](evidence/03-info-plist.txt)). The Photos prompt reads, verbatim:

> "Muse **syncs your photos and videos** for content understanding and media editing"

## 2. Architecture: your Mac as a node for a Meta VM

The app is a thin native Swift shell around a 53 MB web UI (`Resources/hatch/index.html`). The bundle contains the following remote-agent integration evidence:

- VM leasing/release endpoints are present (`/hatch/fetch_leased_vm`, `/hatch/destroy_and_release_vm`, `.metaaivm.com`).
- The client implements a WebSocket gateway connection and **exposes local tools**.
- Backend hosts found in the binary: `agent.meta.ai`, `hatch-api.meta.ai`, `api.meta.ai`, `meta.graph.meta.com`, `auth.meta.com`, plus gateway hosts `node.hatch.one` and `*.customer.prod.willow606.com`.
- Tool-call text in the binary tells the model to `"Use files.upload to copy the complete file to the VM."`

These are cloud-agent pathways, not evidence that all processing stays on-device. The exact data sent depends on the operation and permissions. Meta’s published cloud architecture is summarized in [§12](#12-current-public-disclosures-and-release-status).

## 3. What it can read

Tool names compiled into `Contents/MacOS/Muse` ([`evidence/04-agent-tools.txt`](evidence/04-agent-tools.txt)):

| Area | Tools |
|---|---|
| **iMessage** | `imessage.search` `imessage.get` `imessage.threads` `imessage.send` `imessage.attachment` `imessage.save_attachment` |
| **WhatsApp** | `whatsapp.search` |
| **Email** (Mail.app) | `email.search` `email.read` `email.send` `email.delete` |
| **Notes** | `notes.search` `notes.list` `notes.read` `notes.folders` `notes.create` |
| **Calendar** | `calendar.list` `calendar.events` `calendar.search` `calendar.create` `calendar.update` `calendar.delete` |
| **Reminders** | `reminders.list` `reminders.create` `reminders.update` `reminders.complete` `reminders.delete` |
| **Contacts** | `contacts.search` |
| **Files** | `files.read` `files.write` `files.edit` `files.search` `files.list` `files.upload` `files.trash` `files.copy` `files.mkdir` `files.subscribe` |
| **Screen / input** | `computer.observe` `computer.control` `computer.session` `screen.snap` `screen.recorder` |
| **Camera** | `camera.session` |

### iMessage: read straight from the database

The binary contains an `IMessageReader`, `IMessageDBSchema` and `EndoIMessageSyncSource`. From the tool description:

> "Extract one downloaded attachment from a visible message on this Mac … Returns the original file bytes, including photos and PDFs … **Requires Full Disk Access** and iMessage read permission. … Does not mark the message read."

Reading `~/Library/Messages/chat.db` requires Full Disk Access. **Full Disk Access extends access beyond Messages** to other privacy-protected data; it does not grant root, bypass every protection, or independently authorize all Muse tools.

### WhatsApp: reading another app's private database

Muse ships with hard-coded paths into WhatsApp's sandbox containers ([`evidence/06-data-access-strings.txt`](evidence/06-data-access-strings.txt)):

```
Library/Containers/net.whatsapp.WhatsApp
Library/Containers/desktop.WhatsApp
Library/Containers/net.whatsapp.WhatsAppInhouse
ChatStorage.sqlite
```

> "Search text messages in the primary account of the WhatsApp desktop app installed on this Mac. … **Advanced Chat Privacy, locked and hidden chats** … are excluded. … Requires the user's consent for WhatsApp on this Mac and Full Disk Access."

This is an endpoint-access pathway to WhatsApp’s **local plaintext database**, subject to the stated exclusions and permissions. It is not a demonstrated break of WhatsApp’s transport encryption. Search results can include other participants’ messages; this review cannot establish what those participants consented to or which results were transmitted in practice.

### Mail, Notes, Messages via AppleScript

```
tell application "Mail"
tell application "Messages"
tell application id "com.apple.Notes"
```

### What it refuses

To be fair: the file tools explicitly reject `~/.ssh`, `~/.gnupg`, `~/.aws`, keychains and password stores:

> "Credential files (keychains, ~/.ssh, ~/.gnupg, ~/.aws, a password store) are rejected."

These tool descriptions state a credential-file restriction; they do not prove enforcement across every possible screen or browser pathway. Nor does the presence of screen-control tools prove a bypass of credential protections. The cloud browser and this local extension should be assessed separately.

## 4. What it uploads in the background

The app contains a **sync engine** for sending personal data to its gateway after the relevant access and sync settings are enabled; collection is not limited to individual search requests ([`evidence/05-sync-and-upload-strings.txt`](evidence/05-sync-and-upload-strings.txt)).

**Sync sources compiled into the binary:**

```
EndoIMessageSyncSource     EndoEmailSyncSource      EndoNotesSyncSource
EndoCalendarSyncSource     EndoRemindersSyncSource  EndoContactsSyncSource
NodeDataSyncSource         NodeBackfillUploadState  EndoBackfillResumeStore
```

**Backfill:** support for importing historical data, with scope depending on the source and requested window:

> "Data source id to backfill. Supported: **imessage, email, calendar, notes, reminders, contacts**."

It contains resumable-upload state (`BackfillResumeStore`, `NodeBackfillUploadState`), consistent with continuing interrupted backfills. Restart recovery was not tested.

**Deltas:** strings describe subsequent change uploads and snapshots:

```
[EndoCalendarSyncSource] Delta (
[EndoContactsSyncSource] Full snapshot (
[EndoEmailSyncSource] Forward encode failed; keeping cursor
```

**The consent copy** in the web UI ([`evidence/07-autosync-consent-copy.txt`](evidence/07-autosync-consent-copy.txt)), shown under the friendly heading "Keep ___ up to date":

> **Keep messages up to date:** "New messages are shared automatically. Turn this off to share only what you ask for."
> **Keep email up to date:** "Who new email is from and what it is about are shared automatically. **The message text is shared only when you ask.**"
> **Keep notes up to date:** "New and edited notes are shared automatically."
> **Keep calendar / reminders / contacts up to date:** "New and changed … are shared automatically."

The copy describes automatic sharing, but expressly distinguishes email metadata from body text. The web UI reads connector `autoSync.enabled` state and sends changes through `setLocalConnectorAutoSync` to native code. One consent-dialog initializer falls back to `true` when that state is missing (`Wi?.autoSync.enabled??!0`). This is **not proof that every connector defaults on or that the server can override a user’s choice**. The native binary also contains `nodeAutoSync.` preference keys and sync-disabled paths. See [the additional evidence](evidence/12-permission-and-pairing-review.txt).

**Photos (MediaSync)** runs as its own background uploader:

```
[MediaSync] Starting background sync timer
[MediaSync] Found
[MediaSync] Uploaded
[MediaSync] Already on server:
[MediaSync] Sync complete: everything up to date
media_sync_manifest.json
media_sync_enabled
```

These strings establish background media-upload and deduplication machinery. **They do not establish the selected date range, media types, default enablement or that the entire library is uploaded.** `media_sync_last_date` and permission/skip paths are also present. The previous whole-library conclusion was too strong.

## 5. Full computer control

Muse asks for **Accessibility** and **Screen Recording**:

```
 prompting and waiting for Accessibility and Screen Recording
fbobjc/Apps/Internal/Endo/Sources/Shared/HatchTools/ScreenCapture.swift
AXUIElement
Accessibility action that hides the computer-control preview while Hatch keeps working
```

These permissions support broad screen observation and input automation. Sensitive information visible in ordinary windows may be exposed, but protected surfaces and actual approval enforcement were not tested. The preview-hiding accessibility label shows a UI option to hide a preview while work continues; it does not establish covert execution or suppression of macOS privacy indicators.

## 6. The Chrome extension: broad debugger access

`Resources/chrome/` is a Manifest V3 extension called **"Muse Browser Node"**, "Connects your browser to Muse as a controllable node" ([`evidence/08-chrome-extension-manifest.json`](evidence/08-chrome-extension-manifest.json), [`evidence/09-browser-extension.txt`](evidence/09-browser-extension.txt)).

```json
"permissions": ["tabs","activeTab","scripting","downloads","history","bookmarks",
                "notifications","storage","debugger","alarms","webNavigation"],
"host_permissions": ["<all_urls>"],
"externally_connectable": { "ids": ["*"] }
```

- **`debugger` + `<all_urls>`** requests broad browser access. The extension implements page reads, screenshots and input through Chrome DevTools Protocol. This requires installation, pairing and a permitted target; the manifest alone does not mean it reads every visited page. [Chrome permission documentation](https://developer.chrome.com/docs/extensions/develop/concepts/declare-permissions) also describes separate incognito/file-access controls.
- **`history` + `bookmarks` + `downloads`** give it your browsing history, bookmarks and downloads list.
- The commands it exposes to the remote agent: `tabs.list/open/close/navigate`, `page.content`, `page.screenshot`, `page.click`, `page.type`, `page.fill_form`, `history.search`, `bookmarks.search`, `downloads.list`.
- **Local blocklist:** contains `agent.meta.ai`, `hatch.meta.ai`, `hatch.ecto1.ai`, `muse.ai`, `internalfb.com` and WhatsApp domains. It is not a general bank/email/SSO blocklist. Non-web schemes are also rejected, with an `about:blank` exception. Absence from this list does not prove that an action is authorized by the remote service; motive cannot be inferred from the list.
- `externally_connectable: {"ids": ["*"]}` permits messages from other extension IDs, but no `onMessageExternal` handler was found in the shipped JavaScript. **No working external-message control path was demonstrated.**

**Pairing controls omitted from the original report:** web pairing checks sender/event origins against `https://hatch.meta.ai` and `https://agent.meta.ai`, restricts gateway hostnames and requires `wss:` for web-issued credentials. Manual pairing has a different URL policy. These checks are visible in [the additional evidence](evidence/12-permission-and-pairing-review.txt); this is not a full security audit.

## 7. `stealth.min.js`: a bot-detection evasion kit

`Resources/stealth.min.js` (180 KB) opens with:

```
 * Generated by: https://github.com/berstend/puppeteer-extra/tree/master/packages/extract-stealth-evasions
```

This is **puppeteer-extra-plugin-stealth**. Its job is to make an automated browser look human to anti-bot systems by faking `navigator.webdriver`, `chrome.runtime`, plugins, languages, WebGL vendor and `hardwareConcurrency` ([`evidence/10-stealth-js.txt`](evidence/10-stealth-js.txt)).

It isn't referenced by filename in the native binary, the web bundle or the extension, so it may be loaded indirectly or be unused. Bundling these browser-fingerprinting evasions is a finding; **execution and use against any particular site remain unverified**. The extension separately contains `cursor-overlay.js` and a managed-browser debugging-port constant (`9222`).

## 8. Is Muse spyware?

**This static review does not establish spyware, malicious intent, covert collection or a security exploit.** It establishes a broad set of data-access and remote-control capabilities that deserve informed consent and independent testing.

The meaningful questions are which connectors are enabled, what information they send, whether approvals are enforced, who can access the stored data, whether it is used for training, and what deletion actually removes. A signature or a permission prompt does not answer all of those questions. Conversely, a powerful API or an upload string alone does not prove unauthorized surveillance.

Shared messages, contacts and photos can also contain information about people other than the account holder. That is a real privacy consideration, without assuming anything about each person's consent.

## Meta's track record

Historical context can inform trust, but it is **not evidence that Muse repeats these practices**.

- **Onavo / Project Ghostbusters:** reporting on court filings unsealed in March 2024 described interception of encrypted competitor-app traffic for analytics, including Snapchat, YouTube and Amazon. Treat the filings and reporting as their respective sources, not a Muse finding. [The Register](https://www.theregister.com/2024/03/27/meta_snapchat_data/).
- **Facebook Research (2019):** reporting described payments of up to $20 per month to participants aged 13–35 for installing a traffic-monitoring VPN through enterprise distribution. A trusted root certificate used for interception is **not equivalent to rooting a phone** or unrestricted filesystem access. [MacRumors](https://www.macrumors.com/2019/01/29/facebook-sideloading-vpn-app/).
- **Onavo penalty (2023):** the Australian Federal Court ordered Facebook Israel and Onavo to pay A$10 million each over misleading conduct concerning data use. [ACCC, 26 July 2023](https://www.accc.gov.au/media-release/20m-penalty-for-meta-companies-for-conduct-liable-to-mislead-consumers-about-use-of-their-data).
- **FTC settlement (2019):** Facebook agreed to a US$5 billion penalty and privacy restrictions to settle allegations that it violated its 2012 FTC order. [FTC, 24 July 2019](https://www.ftc.gov/news-events/news/press-releases/2019/07/ftc-imposes-5-billion-penalty-sweeping-new-privacy-restrictions-facebook).
- **Localhost tracking (2025 disclosure):** researchers documented Facebook/Instagram Android apps receiving website identifiers over localhost, linking browser activity to app identities despite incognito/cookie protections. Their update says Meta Pixel stopped this localhost traffic on 3 June 2025. The research site now also links its USENIX Security 2026 paper. **This was not demonstrated in Muse.** [Original researchers](https://localmess.github.io/).

## 10. If you already installed it

1. **Turn off every "Keep ___ up to date" switch** in Muse's connector settings.
2. **Turn off media / Photos sync.**
3. **Revoke in System Settings → Privacy & Security:** Full Disk Access, Accessibility, Screen Recording, Automation, Photos, Contacts, Calendars, Reminders, Camera, Microphone, Location.
4. **Remove the "Muse Browser Node" extension** from every Chrome profile (`chrome://extensions`).
5. Quit Muse and remove `/Applications/Muse.app`. To **list** possible leftovers for review, use `find ~/Library -iname '*com.meta.endo*'`; this command does not delete anything.
6. Disconnect connectors and use Muse’s current account/data controls to request removal of cloud data. **Uninstalling is not evidence of server deletion.** This review has not verified retention periods, backup deletion or an Accounts Center workflow for Muse.
7. If you keep using Muse, review the training-data setting described in §12 and consider what information about other people your connectors share.

## 11. Reproduce it yourself

```bash
git clone https://github.com/mahdi-salmanzade/meta-muse-teardown.git
cd meta-muse-teardown
./scripts/reproduce.sh ~/Downloads/Muse-3.0.dmg
```

Requires macOS command-line tools and Python 3. The script mounts the DMG **read-only**, copies the app into a temporary directory, inspects signatures/plists/strings/resources and prints the core Mac findings. It never launches Muse and cleans up the temporary copy on exit. It does **not** regenerate every historical evidence file byte-for-byte.

For the new review evidence, use Python 3 and the extracted samples:

```bash
python3 scripts/collect-review-evidence.py mac extracted/Muse.app --output /tmp/muse-mac-review
python3 scripts/collect-review-evidence.py android extracted-apk/jadx/sources evidence-android --output /tmp/muse-android-review
python3 scripts/collect-review-evidence.py ios com.facebook.hatch_8.1_und3fined.ipa extracted-ipa/Payload/HatchApp.app --output /tmp/muse-ios-review
python3 scripts/collect-review-evidence.py release --output /tmp/muse-release-review
```

The first three commands are local static inspection; `release` alone fetches the public production update feed. The Android command requires an existing JADX extraction and the manifest-permission evidence. The iOS command requires macOS command-line tools and records signature failures instead of treating displayed certificate metadata as verification. Platform reports describe extraction and verification commands.

| File | What it shows |
|---|---|
| [`evidence/01-signature.txt`](evidence/01-signature.txt) | DMG hash, Meta Developer ID signature, notarization |
| [`evidence/02-entitlements.txt`](evidence/02-entitlements.txt) | Entitlements (no sandbox; camera, mic, contacts, photos, Apple Events) |
| [`evidence/03-info-plist.txt`](evidence/03-info-plist.txt) | Info.plist incl. every privacy prompt (client tokens redacted) |
| [`evidence/04-agent-tools.txt`](evidence/04-agent-tools.txt) | Local tool names exposed to the remote agent |
| [`evidence/05-sync-and-upload-strings.txt`](evidence/05-sync-and-upload-strings.txt) | Backfill, delta sync and MediaSync strings |
| [`evidence/06-data-access-strings.txt`](evidence/06-data-access-strings.txt) | iMessage, WhatsApp, AppleScript, screen capture, VM endpoints |
| [`evidence/07-autosync-consent-copy.txt`](evidence/07-autosync-consent-copy.txt) | The exact "Keep ___ up to date" consent wording |
| [`evidence/08-chrome-extension-manifest.json`](evidence/08-chrome-extension-manifest.json) | Browser extension permissions |
| [`evidence/09-browser-extension.txt`](evidence/09-browser-extension.txt) | Blocklist, exposed commands, allowed gateway hosts |
| [`evidence/10-stealth-js.txt`](evidence/10-stealth-js.txt) | puppeteer-extra stealth evasion header |
| [`evidence/11-feature-flags.txt`](evidence/11-feature-flags.txt) | Feature-flag names; names do not establish enabled rollout |
| [`evidence/12-permission-and-pairing-review.txt`](evidence/12-permission-and-pairing-review.txt) | Native sync bridge, consent-state initializer, browser pairing controls |
| [`evidence/13-release-feed.json`](evidence/13-release-feed.json) | Dated production-feed metadata without transient CDN query strings |

## 12. Current public disclosures and release status

Checked **2026-09-24**. Statements below are attributed to their publishers; the server protections were not independently tested.

**Release status.** Meta announced Muse on **8 September 2026**, initially rolling out in the US on iOS, Android and the web. [Meta launch announcement](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/). The live Mac production feed lists **3.0 / 1075746581**, matching the inspected bundle and DMG size ([captured metadata](evidence/13-release-feed.json)). The US App Store lists **8.1**, matching the iOS sample’s marketing version; this does not authenticate the sample. [App Store](https://apps.apple.com/us/app/muse-from-meta/id6760173601). Android’s newest distributed version was not established in this review.

**What Meta says about privacy and security.** Its 8 September technical post describes:

- **Training enabled by default:** conversations, tool calls and subagent handoffs may train models after removal of key personally identifying information; users can opt out in Muse settings.
- **Advertising:** conversations and VM data are not shared with Meta’s ad systems, although websites visited by Muse can influence advertising indirectly.
- **Provider access:** current VM protections do not cryptographically prevent Meta access needed to operate the service. **Confidential VM** was announced for later in 2026, with limited testing; general availability was not verified here.
- **Security controls:** separate credential storage and Sentinel authorization, scoped approvals, isolation of the agent runtime, and filters for email OTPs/reset links. These are vendor descriptions, not independently verified guarantees or proof of equivalent filtering for Android SMS/notifications.

Source: [Meta, How We Built Safety Into Muse](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse).

**Newer announcement.** On **23 September 2026**, Meta announced Muse integration for its AI glasses. This expands the announced product scope; the three local samples do not establish what glasses collect or when each feature becomes available. [Meta’s Connect announcement (Spanish)](https://about.fb.com/ltam/news/2026/09/tu-agente-personal-llega-a-los-lentes-con-ia/).

The App Store’s linked [Muse privacy page](https://muse.ai/privacy) required login during this review. No claims about its unseen text, exact retention periods or deletion guarantees are made here.

---

*Independent research by the repo owner, not affiliated with Meta. Analysis date: 2026-09-24. Static analysis only; the app was never run. If Meta disputes any finding, open an issue with specifics and it'll be corrected.*
