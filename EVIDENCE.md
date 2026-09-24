# Complete evidence index

[**iOS report**](IOS.md) · [**macOS report**](README.md) · [**Android report**](ANDROID.md) · [**Review log**](REVIEW.md) · [**Commit audit**](COMMIT-AUDIT.md)

Every evidence file in the three folders is linked below. Original extraction notes are retained; new machine-readable files supplement them. Interpretive prose in older notes is not itself proof of runtime behavior. The platform reports explain corrections and the iOS sample’s failed integrity verification.

The checksums establish the identity of the repository’s evidence files, not the authenticity of claims or of the original apps. Verify them from the repository root:

```bash
shasum -a 256 -c evidence.sha256
```

The app archives, full extracted binaries and full decompiled source are excluded; the repository publishes hashes, metadata, bounded extracts and commentary. See the [reproduction instructions](README.md#11-reproduce-it-yourself) for which extracts can be rebuilt automatically. The banner is editorial artwork, not a captured application screenshot or technical evidence.

**Total: 53 evidence files.**

## iOS — 19 files

| Evidence file | Format |
|---|---|
| [01-authenticity.txt](evidence-ios/01-authenticity.txt) | TXT |
| [01-provenance.txt](evidence-ios/01-provenance.txt) | TXT |
| [02-info-plist.json](evidence-ios/02-info-plist.json) | JSON |
| [02-info-plist.txt](evidence-ios/02-info-plist.txt) | TXT |
| [03-entitlements.json](evidence-ios/03-entitlements.json) | JSON |
| [03-entitlements.txt](evidence-ios/03-entitlements.txt) | TXT |
| [04-command-names.txt](evidence-ios/04-command-names.txt) | TXT |
| [04-extensions.txt](evidence-ios/04-extensions.txt) | TXT |
| [05-agent-tools.txt](evidence-ios/05-agent-tools.txt) | TXT |
| [05-sync-and-consent.txt](evidence-ios/05-sync-and-consent.txt) | TXT |
| [06-sync-upload.txt](evidence-ios/06-sync-upload.txt) | TXT |
| [07-health.txt](evidence-ios/07-health.txt) | TXT |
| [08-location.txt](evidence-ios/08-location.txt) | TXT |
| [09-endpoints.txt](evidence-ios/09-endpoints.txt) | TXT |
| [10-notable.txt](evidence-ios/10-notable.txt) | TXT |
| [11-health-import-count.txt](evidence-ios/11-health-import-count.txt) | TXT |
| [12-extension-metadata.json](evidence-ios/12-extension-metadata.json) | JSON |
| [15-consent-retention-ios.txt](evidence-ios/15-consent-retention-ios.txt) | TXT |
| [16-network-ios.txt](evidence-ios/16-network-ios.txt) | TXT |

## macOS and cross-platform — 19 files

| Evidence file | Format |
|---|---|
| [01-signature.txt](evidence/01-signature.txt) | TXT |
| [02-entitlements.txt](evidence/02-entitlements.txt) | TXT |
| [03-info-plist.txt](evidence/03-info-plist.txt) | TXT |
| [04-agent-tools.txt](evidence/04-agent-tools.txt) | TXT |
| [05-sync-and-upload-strings.txt](evidence/05-sync-and-upload-strings.txt) | TXT |
| [06-data-access-strings.txt](evidence/06-data-access-strings.txt) | TXT |
| [07-autosync-consent-copy.txt](evidence/07-autosync-consent-copy.txt) | TXT |
| [08-chrome-extension-manifest.json](evidence/08-chrome-extension-manifest.json) | JSON |
| [09-browser-extension.txt](evidence/09-browser-extension.txt) | TXT |
| [10-stealth-js.txt](evidence/10-stealth-js.txt) | TXT |
| [11-feature-flags.txt](evidence/11-feature-flags.txt) | TXT |
| [12-permission-and-pairing-review.txt](evidence/12-permission-and-pairing-review.txt) | TXT |
| [13-release-feed.json](evidence/13-release-feed.json) | JSON |
| [14-extension-token-lifecycle.txt](evidence/14-extension-token-lifecycle.txt) | TXT |
| [15-consent-retention-macos.txt](evidence/15-consent-retention-macos.txt) | TXT |
| [15-public-statements-vs-app.txt](evidence/15-public-statements-vs-app.txt) | TXT |
| [16-network-cross-platform.txt](evidence/16-network-cross-platform.txt) | TXT |
| [16-network-macos.txt](evidence/16-network-macos.txt) | TXT |
| [17-commit-audit.txt](evidence/17-commit-audit.txt) | TXT |

## Android — 15 files

| Evidence file | Format |
|---|---|
| [01-signature.txt](evidence-android/01-signature.txt) | TXT |
| [02-permissions.txt](evidence-android/02-permissions.txt) | TXT |
| [03-manifest-components.txt](evidence-android/03-manifest-components.txt) | TXT |
| [04-agent-commands.txt](evidence-android/04-agent-commands.txt) | TXT |
| [05-proactive-sync-and-backfill.txt](evidence-android/05-proactive-sync-and-backfill.txt) | TXT |
| [06-notification-listener.txt](evidence-android/06-notification-listener.txt) | TXT |
| [07-health-and-location.txt](evidence-android/07-health-and-location.txt) | TXT |
| [08-photos.txt](evidence-android/08-photos.txt) | TXT |
| [09-notable.txt](evidence-android/09-notable.txt) | TXT |
| [10-review-corrections.txt](evidence-android/10-review-corrections.txt) | TXT |
| [11-health-permission-count.txt](evidence-android/11-health-permission-count.txt) | TXT |
| [12-phone-id-provider.txt](evidence-android/12-phone-id-provider.txt) | TXT |
| [13-publish-path-gating.txt](evidence-android/13-publish-path-gating.txt) | TXT |
| [15-consent-retention-android.txt](evidence-android/15-consent-retention-android.txt) | TXT |
| [16-network-android.txt](evidence-android/16-network-android.txt) | TXT |
