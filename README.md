# Muse by Meta: what it actually takes from your Mac

A teardown of **Muse 3.0 for macOS** (`Muse-3.0.dmg`), Meta's desktop AI agent, internally codenamed **Endo / Hatch**.

**TL;DR:** Muse is a genuine, Meta-signed app. Once you grant its permissions, it:

- reads your **iMessage history** straight out of the Messages database
- reads your **WhatsApp chats** straight out of WhatsApp's SQLite file
- keeps **uploading new messages, notes, calendar events, reminders and contacts** to Meta in the background
- uploads your **Photos library** on a timer
- can **see your screen and click and type** anywhere on your Mac
- installs a **Chrome extension with debugger access to every website you visit**

The "brain" of the agent doesn't run on your computer. It runs in a **Meta-hosted virtual machine** (`*.metaaivm.com`), and your Mac is wired up as its remote-controlled "node".

This is the company that ran a VPN called Onavo to [decrypt Snapchat, YouTube and Amazon traffic from its own users](#metas-track-record) and paid teenagers $20 a month to install a root-certificate "research" app. Read what Muse does before you click "Allow".

### Platforms covered

| Platform | Build | Report |
|---|---|---|
| macOS | Muse 3.0 (`com.meta.endo`) | this page |
| Android | 8.0.0.21.168 (`com.facebook.aura`), Play-signed | **[ANDROID.md](ANDROID.md)**: SMS, call log, **every app's notifications (default: all apps, no 2FA filter)**, background location, 20+ Health Connect types published proactively |

> Every claim below points to a file in [`evidence/`](evidence/) and can be rebuilt from your own copy of the DMG with [`scripts/reproduce.sh`](scripts/reproduce.sh). This repo contains **no Meta binaries or source**, only hashes, `strings`/`grep` output and short excerpts for commentary.

---

## Contents

1. [Is this really Meta's app?](#1-is-this-really-metas-app)
2. [Architecture: your Mac as a node for a Meta VM](#2-architecture-your-mac-as-a-node-for-a-meta-vm)
3. [What it can read](#3-what-it-can-read)
4. [What it uploads in the background](#4-what-it-uploads-in-the-background)
5. [Full computer control](#5-full-computer-control)
6. [The Chrome extension: debugger on every site](#6-the-chrome-extension-debugger-on-every-site)
7. [`stealth.min.js`: a bot-detection evasion kit](#7-stealthminjs-a-bot-detection-evasion-kit)
8. [Is Muse spyware?](#8-is-muse-spyware)
9. [Meta's track record](#metas-track-record)
10. [If you already installed it](#10-if-you-already-installed-it)
11. [Reproduce it yourself](#11-reproduce-it-yourself)

---

## 1. Is this really Meta's app?

Yes. This is not a trojan pretending to be Meta. The code signature, notarization and provisioning profile all belong to Meta Platforms, Inc. ([`evidence/01-signature.txt`](evidence/01-signature.txt)).

| Field | Value |
|---|---|
| DMG sha256 | `3818f35b89580d857f412977f6d8f5d409dbc3112da3e7119ea254d518010de4` |
| Bundle ID | `com.meta.endo` |
| Version | 3.0 (build `1075746581`), release channel `production` |
| Signed by | `Developer ID Application: Meta Platforms, Inc. (V9WTTPBFK9)` |
| Gatekeeper | `accepted`, `source=Notarized Developer ID` |
| Provisioning profile | "Endo Hatch MacOS Developer ID Application", Team "Meta Platforms, Inc." |
| Update feed | `https://www.facebook.com/endo/release/appcast.xml?channel=production` (Sparkle) |
| Source paths leaked in binary | `fbobjc/Apps/Internal/Endo/Sources/...` |

It is **not App-Sandboxed**: there is no `com.apple.security.app-sandbox` entitlement ([`evidence/02-entitlements.txt`](evidence/02-entitlements.txt)). Anything the process can reach as your user, it can reach.

Entitlements granted:

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

The app is a thin native Swift shell around a 53 MB web UI (`Resources/hatch/index.html`). The agent itself runs remotely:

- Meta leases a **VM per user** (`/hatch/fetch_leased_vm`, `/hatch/destroy_and_release_vm`, `.metaaivm.com`).
- Your Mac connects to that VM's gateway over WebSocket and **exposes local tools to it**.
- Backend hosts found in the binary: `agent.meta.ai`, `hatch-api.meta.ai`, `api.meta.ai`, `meta.graph.meta.com`, `auth.meta.com`, plus gateway hosts `node.hatch.one` and `*.customer.prod.willow606.com`.
- Tool-call text in the binary tells the model to `"Use files.upload to copy the complete file to the VM."`

In other words, **your data leaves the machine to reach the agent**. It doesn't just sit locally for an on-device model.

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

Reading `~/Library/Messages/chat.db` requires Full Disk Access. **Once you grant Full Disk Access, the app can read every file your user account can read**, not just Messages.

### WhatsApp: reading another app's private database

Muse ships with hard-coded paths into WhatsApp's sandbox containers ([`evidence/06-data-access-strings.txt`](evidence/06-data-access-strings.txt)):

```
Library/Containers/net.whatsapp.WhatsApp
Library/Containers/desktop.WhatsApp
Library/Containers/net.whatsapp.WhatsAppInhouse
ChatStorage.sqlite
```

> "Search text messages in the primary account of the WhatsApp desktop app installed on this Mac. … **Advanced Chat Privacy, locked and hidden chats** … are excluded. … Requires the user's consent for WhatsApp on this Mac and Full Disk Access."

Meta owns WhatsApp, so this is Meta's own product reading the end-to-end-encrypted messenger's **decrypted local store** and sending search results to a Meta cloud VM. The "E2E encrypted" promise covers messages in transit. It says nothing about a second Meta app reading them off your disk. The other people in your chats never agreed to this.

### Mail, Notes, Messages via AppleScript

```
tell application "Mail"
tell application "Messages"
tell application id "com.apple.Notes"
```

### What it refuses

To be fair: the file tools explicitly reject `~/.ssh`, `~/.gnupg`, `~/.aws`, keychains and password stores:

> "Credential files (keychains, ~/.ssh, ~/.gnupg, ~/.aws, a password store) are rejected."

That rule applies to the `files.*` tools. It doesn't limit what `computer.control` can see on screen or what the Chrome extension can read in your browser.

## 4. What it uploads in the background

This is the core problem. Muse doesn't only fetch data when you ask a question. It has a **sync engine** that pushes your personal data to Meta continuously ([`evidence/05-sync-and-upload-strings.txt`](evidence/05-sync-and-upload-strings.txt)).

**Sync sources compiled into the binary:**

```
EndoIMessageSyncSource     EndoEmailSyncSource      EndoNotesSyncSource
EndoCalendarSyncSource     EndoRemindersSyncSource  EndoContactsSyncSource
NodeDataSyncSource         NodeBackfillUploadState  EndoBackfillResumeStore
```

**Backfill:** a bulk import of your existing history:

> "Data source id to backfill. Supported: **imessage, email, calendar, notes, reminders, contacts**."

It has resumable upload state (`BackfillResumeStore`, `NodeBackfillUploadState`), so a partial upload survives restarts.

**Deltas:** after the backfill, changes stream up:

```
[EndoCalendarSyncSource] Delta (
[EndoContactsSyncSource] Full snapshot (
[EndoEmailSyncSource] Forward encode failed; keeping cursor
```

**The consent copy** in the web UI ([`evidence/07-autosync-consent-copy.txt`](evidence/07-autosync-consent-copy.txt)), shown under the friendly heading "Keep ___ up to date":

> **Keep messages up to date:** "New messages are shared automatically. Turn this off to share only what you ask for."
> **Keep email up to date:** "Who new email is from and what it is about are shared automatically."
> **Keep notes up to date:** "New and edited notes are shared automatically."
> **Keep calendar / reminders / contacts up to date:** "New and changed … are shared automatically."

"Shared" means **uploaded to Meta**. Note the framing: the privacy-preserving choice is worded as the thing you have to *turn off*. Whether each switch starts on or off is decided **server-side** (`autoSync.enabled` arrives from Meta's config), so Meta can change the default without shipping a new app.

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

`Already on server` and `everything up to date` describe a system meant to mirror your **entire library** to Meta, not one photo you chose to attach.

## 5. Full computer control

Muse asks for **Accessibility** and **Screen Recording**:

```
 prompting and waiting for Accessibility and Screen Recording
fbobjc/Apps/Internal/Endo/Sources/Shared/HatchTools/ScreenCapture.swift
AXUIElement
Accessibility action that hides the computer-control preview while Hatch keeps working
```

With both granted, the remote agent can capture any window and type or click into any app: banking apps, password managers, 2FA prompts, all of it. The string about *hiding the computer-control preview while Hatch keeps working* means the agent is designed to keep operating your Mac after you've tucked away its on-screen indicator.

## 6. The Chrome extension: debugger on every site

`Resources/chrome/` is a Manifest V3 extension called **"Muse Browser Node"**, "Connects your browser to Muse as a controllable node" ([`evidence/08-chrome-extension-manifest.json`](evidence/08-chrome-extension-manifest.json), [`evidence/09-browser-extension.txt`](evidence/09-browser-extension.txt)).

```json
"permissions": ["tabs","activeTab","scripting","downloads","history","bookmarks",
                "notifications","storage","debugger","alarms","webNavigation"],
"host_permissions": ["<all_urls>"],
"externally_connectable": { "ids": ["*"] }
```

- **`debugger` + `<all_urls>`** lets it drive the Chrome DevTools Protocol on any tab. It can read the full page (including logged-in sessions), screenshot it, type into forms and click buttons.
- **`history` + `bookmarks` + `downloads`** give it your browsing history, bookmarks and downloads list.
- The commands it exposes to the remote agent: `tabs.list/open/close/navigate`, `page.content`, `page.screenshot`, `page.click`, `page.type`, `page.fill_form`, `history.search`, `bookmarks.search`, `downloads.list`.
- **Blocklist:** the only sites the agent is forbidden to drive are Meta's own (`agent.meta.ai`, `hatch.meta.ai`, `muse.ai`, `internalfb.com`) and WhatsApp. **Your bank, your email and your employer's SSO are all allowed.** Meta protected its own properties from its agent and left yours open.
- `externally_connectable: {"ids": ["*"]}` lets *any* installed extension message it. The current code has no `onMessageExternal` listener, so this does nothing today. It's still a wide-open door on an extension with `debugger` power, one update away from mattering.

## 7. `stealth.min.js`: a bot-detection evasion kit

`Resources/stealth.min.js` (180 KB) opens with:

```
 * Generated by: https://github.com/berstend/puppeteer-extra/tree/master/packages/extract-stealth-evasions
```

This is **puppeteer-extra-plugin-stealth**. Its job is to make an automated browser look human to anti-bot systems by faking `navigator.webdriver`, `chrome.runtime`, plugins, languages, WebGL vendor and `hardwareConcurrency` ([`evidence/10-stealth-js.txt`](evidence/10-stealth-js.txt)).

It isn't referenced by filename in the native binary, the web bundle or the extension, so it may be loaded indirectly or be unused. Either way, **Meta shipped a tool whose only purpose is to defeat websites' ability to tell they're talking to a bot.** It fits with the extension's `cursor-overlay.js` and "managed Chromium" mode (`MANAGED_BROWSER_DEBUG_PORT = '9222'`).

## 8. Is Muse spyware?

Muse asks before each permission. It isn't hidden, and it's signed and notarized by Meta. By the narrow definition ("software installed without consent"), it isn't spyware.

**By function, it's hard to tell apart from spyware:**

| Typical spyware capability | Muse |
|---|---|
| Read SMS / iMessage | ✅ `imessage.search`, direct `chat.db` read via Full Disk Access |
| Read WhatsApp | ✅ reads `ChatStorage.sqlite` |
| Read email | ✅ `email.search` / `email.read` |
| Contacts, calendar | ✅ plus continuous delta upload |
| Photo library exfiltration | ✅ MediaSync background uploader |
| Screen capture | ✅ ScreenCaptureKit |
| Remote keyboard / mouse control | ✅ Accessibility (`computer.control`) |
| Browser history + live page content | ✅ Chrome extension with `debugger` on `<all_urls>` |
| Camera / microphone | ✅ entitlements + `camera.session` |
| Data sent to a remote operator | ✅ Meta-hosted VM, `*.metaaivm.com` |
| Background persistence of uploads | ✅ resumable backfill, timers, deltas |

The only difference between this and stalkerware is **who the operator is** and the fact that **you clicked "Allow"**. The operator is Meta, which has repeatedly been caught, fined and sued for collecting more than it said it would (next section). The "Allow" is a one-time click with friendly wording, and the upload switches are under server control.

Your consent also doesn't cover the other people in your iMessage threads, WhatsApp groups, contacts and photos. Their data goes to Meta too, and they never saw a prompt.

## Meta's track record

Why the operator matters. All of the following is public record.

### Onavo & "Project Ghostbusters": decrypting Snapchat traffic (2016–2019)

- Facebook bought the Israeli VPN company **Onavo** in 2013 and marketed **Onavo Protect** as a free privacy VPN. The FTC later described Onavo as a "user surveillance company".
- In June 2016, **Mark Zuckerberg** emailed executives: *"Whenever someone asks a question about Snapchat, the answer is usually that because their traffic is encrypted we have no analytics about them."* He asked for a way to get that data.
- The Onavo team built **"kits" for iOS and Android that intercept traffic for specific sub-domains, "allowing us to read what would otherwise be encrypted traffic"**. This was a **man-in-the-middle** attack run through the VPN on users who had installed it for privacy. Internally it was **Project Ghostbusters**, a reference to Snapchat's ghost logo.
- The same technique was later turned on **YouTube (2017–2018)** and **Amazon (2018)**.
- This came out in **court documents unsealed in March 2024** in the consumer antitrust class action against Meta.

Sources: [TechCrunch](https://techcrunch.com/2024/03/26/facebook-secret-project-snooped-snapchat-user-traffic/) · [The Register](https://www.theregister.com/2024/03/27/meta_snapchat_data/) · [TechRadar](https://www.techradar.com/computing/cyber-security/facebooks-onavo-vpn-used-to-wiretap-competitor-data-court-filings-reveal) · [SFGate](https://www.sfgate.com/tech/article/facebook-snapchat-project-ghostbusters-meta-19373667.php) · [TheStreet](https://www.thestreet.com/technology/how-facebook-used-a-vpn-to-spy-on-what-you-do-on-snap-youtube-and-amazon)

### Onavo Protect pulled from the App Store (2018)

Apple told Facebook that Onavo violated its data-collection rules, and Facebook pulled it from the iOS App Store in August 2018. The Android version was discontinued in 2019.

Sources: [CNBC](https://www.cnbc.com/2018/08/22/apple-removes-facebook-onavo-app-from-app-store.html) · [TechCrunch](https://techcrunch.com/2018/08/22/apple-facebook-onavo/amp)

### "Facebook Research": paying teenagers to install a root-level VPN (2016–2019)

Under **Project Atlas**, Facebook paid people aged **13 to 35** up to **$20 a month** to sideload a "Facebook Research" VPN using an **enterprise certificate**. That gave it root-level access to phone traffic, including **private messages in social media apps**. Facebook hid its involvement behind beta-testing services (Applause, BetaBound, uTest). After TechCrunch exposed it on **29 January 2019**, Apple revoked Facebook's enterprise certificate.

Sources: [MacRumors](https://www.macrumors.com/2019/01/29/facebook-sideloading-vpn-app/) · [Gizmodo](https://gizmodo.com/facebook-is-paying-teens-to-install-a-research-app-that-1832182370) · [TechCrunch](https://techcrunch.com/2019/01/31/mess-with-the-cook/) · [The Register](https://www.theregister.com/2019/01/30/facebook_apple_enterprise_certificate_revocation/)

### A$20 million penalty over Onavo (Australia, 2023)

On **26 July 2023** the Australian Federal Court ordered Facebook Israel Ltd and Onavo Inc to pay **A$10 million each** for misleading consumers. The companies had promoted Onavo Protect as protecting users' data without adequately disclosing that users' app-activity data went to Meta for commercial purposes. The app had over 270,000 Australian installs.

Source: [ACCC](https://www.accc.gov.au/media-release/20m-penalty-for-meta-companies-for-conduct-liable-to-mislead-consumers-about-use-of-their-data)

### US$5 billion FTC penalty (2019)

The largest privacy penalty ever imposed at the time, for violating the 2012 FTC order by **deceiving users about their ability to control their personal information**. It followed the **Cambridge Analytica** scandal, which exposed data on 87 million users.

Source: [FTC](https://www.ftc.gov/news-events/news/press-releases/2019/07/ftc-imposes-5-billion-penalty-sweeping-new-privacy-restrictions-facebook)

### "Local Mess": covert localhost tracking on Android (2024–2025)

Researchers from IMDEA Networks, Radboud University and KU Leuven found that between roughly September 2024 and June 2025, the **Facebook and Instagram Android apps listened on localhost ports**. Meta Pixel scripts on ordinary websites could pass browsing identifiers to them, which tied your web browsing to your logged-in identity **even in incognito mode and behind a VPN**. Meta paused it on 3 June 2025 after disclosure, and Chrome 137 shipped countermeasures.

Sources: [localmess.github.io](https://localmess.github.io/) · [Android Authority](https://www.androidauthority.com/meta-yandex-android-tracking-3563736/)

### The pattern

Every episode has the same shape: **a product sold as useful or protective (a free VPN, a paid "research" program, a login SDK) whose real value to Meta is the data it pulls out**. Muse is presented as a helpful assistant. Technically, it's the broadest data pipe Meta has ever asked a user to install on a computer: messages, WhatsApp, email, photos, screen, keyboard and browser, all routed to a Meta server.

## 10. If you already installed it

1. **Turn off every "Keep ___ up to date" switch** in Muse's connector settings.
2. **Turn off media / Photos sync.**
3. **Revoke in System Settings → Privacy & Security:** Full Disk Access, Accessibility, Screen Recording, Automation, Photos, Contacts, Calendars, Reminders, Camera, Microphone, Location.
4. **Remove the "Muse Browser Node" extension** from every Chrome profile (`chrome://extensions`).
5. Quit Muse, delete `/Applications/Muse.app`, and remove its leftovers: `find ~/Library -iname '*com.meta.endo*'`.
6. Deleting the app doesn't delete what's already been uploaded. Request deletion through Meta's **Accounts Center**, and in the EU/UK file a GDPR Art. 17 erasure request.
7. Tell the people you message. Their messages and photos may have gone too.

## 11. Reproduce it yourself

```bash
git clone <this repo> && cd <repo>
./scripts/reproduce.sh ~/Downloads/Muse-3.0.dmg
```

The script mounts the DMG **read-only**, copies the app bundle out, and runs only `codesign`, `spctl`, `plutil`, `strings` and `grep`. It never launches Muse.

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
| [`evidence/11-feature-flags.txt`](evidence/11-feature-flags.txt) | Server-side feature flags shipped in `metaconfig.json` |

---

*Independent research by the repo owner, not affiliated with Meta. Analysis date: 2026-09-24. Static analysis only; the app was never run. If Meta disputes any finding, open an issue with specifics and it'll be corrected.*
