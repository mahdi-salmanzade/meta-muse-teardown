#!/usr/bin/env python3
"""Build the 2026-09-27 audit's bounded evidence from saved local inputs.

Does not run Muse or connect to any account. Requires macOS tools, Android build
tools, OpenSSL 3, and the extractions described in RELEASE-AUDIT-2026-09-27.md.
Acquisition timestamps come from the saved input files' mtimes, not this run.
"""
import argparse
import base64
import datetime
import hashlib
import json
from pathlib import Path
import plistlib
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--work', type=Path, default=ROOT / 'extracted/release-audit-2026-09-27')
p.add_argument('--output', type=Path, default=ROOT / 'evidence-updates/2026-09-27')
p.add_argument('--build-tools', type=Path, default=Path.home() / 'Library/Android/sdk/build-tools/36.1.0')
p.add_argument('--openssl', default='/opt/homebrew/bin/openssl')
a = p.parse_args()
W, OUT = a.work.resolve(), a.output.resolve()
OLD, NEW = ROOT / 'extracted/Muse.app', W / 'Muse.app'
OUT.mkdir(parents=True, exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)
    (OUT / name).write_text(text.rstrip() + '\n')

def run(args):
    r = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    text = r.stdout + r.stderr
    text = text.replace(str(ROOT), '<repo>').replace(str(W), '<work>')
    return {'exit_code': r.returncode, 'output': text.strip()}

def stamp(path):
    return datetime.datetime.fromtimestamp(path.stat().st_mtime, datetime.timezone.utc).isoformat()

def info(app):
    return plistlib.loads((app / 'Contents/Info.plist').read_bytes())

def inventory(folder):
    return {str(f.relative_to(folder)): sha(f) for f in sorted(folder.rglob('*')) if f.is_file() and not f.is_symlink()}

def delta(old, new):
    return {'added': sorted(new.keys() - old.keys()), 'removed': sorted(old.keys() - new.keys()),
            'changed': [k for k in sorted(old.keys() & new.keys()) if old[k] != new[k]]}

ns = {'sparkle': 'http://www.andymatuschak.org/xml-namespaces/sparkle'}
feed = ET.parse(W / 'appcast.xml')
items = []
for item in feed.findall('./channel/item'):
    e = item.find('enclosure')
    items.append({'version': item.findtext('sparkle:shortVersionString', namespaces=ns),
                  'build': item.findtext('sparkle:version', namespaces=ns),
                  'published': item.findtext('pubDate'), 'bytes': int(e.get('length')),
                  'ed25519_signature': e.get('{' + ns['sparkle'] + '}edSignature')})
apple_html = (W / 'appstore.html').read_text()
apple_recent = []
def visit(x):
    if isinstance(x, dict):
        if x.get('contentType') == 'titledParagraph' and (x.get('impressionMetrics') or {}).get('fields', {}).get('impressionType') == 'versionHistory':
            apple_recent.extend({k: i.get(k) for k in ['primarySubtitle', 'secondarySubtitle', 'text']} for i in x['items'])
        for v in x.values(): visit(v)
    elif isinstance(x, list):
        for v in x: visit(v)
for match in re.finditer(r'<script[^>]*>(.*?)</script>', apple_html, re.S):
    try: visit(json.loads(match[1]))
    except ValueError: pass
if not apple_recent: raise ValueError('No App Store version-history shelf found')
lookup = json.loads((W / 'itunes-lookup.json').read_text())['results'][0]
write('01-release-status.json', {
    'review_date': '2026-09-27',
    'macos': {'source': 'https://www.facebook.com/endo/release/appcast.xml?channel=production',
              'saved_at_utc': stamp(W/'appcast.xml'), 'raw_sha256': sha(W/'appcast.xml'), 'items': items,
              'note': 'Transient signed CDN download URL omitted. Artifact signature verification is in 02.'},
    'ios_web': {'source': 'https://apps.apple.com/us/app/muse-from-meta/id6760173601',
                'saved_at_utc': stamp(W/'appstore.html'), 'raw_sha256': sha(W/'appstore.html'), 'latest_version_shelf': apple_recent},
    'ios_lookup': {'source': 'https://itunes.apple.com/lookup?id=6760173601&country=us',
                   'saved_at_utc': stamp(W/'itunes-lookup.json'),
                   'raw_sha256': sha(W/'itunes-lookup.json'),
                   'fields': {k: lookup[k] for k in ['trackId','bundleId','version','currentVersionReleaseDate']}},
    'ios_limit': 'Website lists 9.0; lookup API returned 8.1. No 9.0 IPA acquired or audited; cannot establish every regional/account rollout.',
    'android': {'acquisition': 'https://d.apkpure.net/b/APK/com.facebook.aura?versionCode=1061401140',
                'saved_at_utc': stamp(W/'Muse-android-9-candidate.apk'),
                'corroborating_catalog': 'https://com-facebook-aura.en.uptodown.com/android',
                'note': 'Third-party artifact, version/signature independently inspected in 03. Not claimed to be the newest build in every Play rollout.'},
})

oldinfo, newinfo = info(OLD), info(NEW)
assert newinfo['CFBundleShortVersionString'] == items[0]['version']
assert newinfo['CFBundleVersion'] == items[0]['build']
assert (W/'Muse-4.1.dmg').stat().st_size == items[0]['bytes']
key = oldinfo['SUPublicEDKey']
assert key == newinfo['SUPublicEDKey']
with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp)
    (temp/'key.der').write_bytes(bytes.fromhex('302a300506032b6570032100') + base64.b64decode(key))
    (temp/'signature').write_bytes(base64.b64decode(items[0]['ed25519_signature']))
    signature = run([a.openssl,'pkeyutl','-verify','-pubin','-keyform','DER','-inkey',temp/'key.der','-rawin','-in',W/'Muse-4.1.dmg','-sigfile',temp/'signature'])
    if signature['exit_code']: raise ValueError('Feed signature verification failed')
    # Negative control: the same feed signature must reject changed artifact bytes.
    tampered = bytearray((W/'Muse-4.1.dmg').read_bytes()); tampered[len(tampered)//2] ^= 1
    (temp/'changed.dmg').write_bytes(tampered)
    rejected = run([a.openssl,'pkeyutl','-verify','-pubin','-keyform','DER','-inkey',temp/'key.der','-rawin','-in',temp/'changed.dmg','-sigfile',temp/'signature'])
    assert rejected['exit_code'] != 0
bundle = {}
entitlements = {}
for label, app in [('baseline',OLD),('current',NEW)]:
    codesign = run(['codesign','--verify','--deep','--strict',app]); assert codesign['exit_code'] == 0
    ent = subprocess.run(['codesign','-d','--entitlements','-','--xml',str(app)],capture_output=True,check=True).stdout
    entitlements[label] = plistlib.loads(ent)
    inf = info(app)
    bundle[label] = {'version': inf['CFBundleShortVersionString'], 'build': inf['CFBundleVersion'],
        'executable_sha256': sha(app/'Contents/MacOS/Muse'), 'integrity': codesign,
        'signing_identity': run(['codesign','-dvvv',app]), 'entitlements': entitlements[label]}
bundle['current']['gatekeeper'] = run(['spctl','-a','-vvv','-t','exec',NEW])
extension_old = inventory(OLD/'Contents/Resources/chrome')
extension_new = inventory(NEW/'Contents/Resources/chrome')
oldfiles,newfiles = inventory(OLD/'Contents'),inventory(NEW/'Contents')
def strings(app):
    return set(subprocess.check_output(['strings','-n','6',str(app/'Contents/MacOS/Muse')]).decode(errors='replace').splitlines())
olds,news = strings(OLD),strings(NEW)
pattern = re.compile(r'AuthCredential|AuthCookie|\[Auth\]|native_credentials|renewed_cookie|approval card|4 KiB', re.I)
tools = re.compile(r'^(?:imessage|email|notes|calendar|reminders|contacts|whatsapp|files|computer|screen|camera)\.[a-z_]+$')
def named_function(app,name):
    s=(app/'Contents/Resources/hatch/index.html').read_text(); start=s.index('function '+name+'(')
    end=s.find('function ',start+len('function ')); return s[start:end]
write('02-macos-comparison.json', {
    'baseline_dmg_sha256': sha(ROOT/'Muse-3.0.dmg'), 'current_dmg_sha256': sha(W/'Muse-4.1.dmg'),
    'feed_signature': signature, 'one_byte_tamper_rejected': True, 'pinned_public_key_from_verified_baseline': key,
    'bundles': bundle, 'bundle_file_delta': delta(oldfiles,newfiles),
    'privacy_usage_descriptions_changed': {k: [oldinfo.get(k),newinfo.get(k)] for k in set(oldinfo)|set(newinfo) if k.endswith('UsageDescription') and oldinfo.get(k)!=newinfo.get(k)},
    'entitlements_equal': entitlements['baseline']==entitlements['current'],
    'extension': {'all_files_identical': extension_old==extension_new,'file_count':len(extension_new),'sha256_by_path':extension_new},
    'selected_tool_names': {'baseline':sorted(filter(tools.match,olds)),'current':sorted(filter(tools.match,news))},
    'autoSyncCopy_extraction_equal': named_function(OLD,'autoSyncCopy')==named_function(NEW,'autoSyncCopy'),
    'selected_added_native_strings': sorted(x for x in news-olds if pattern.search(x) and len(x)<500),
    'native_limits': 'Added strings are investigation leads, not proof of a fixed vulnerability, keychain implementation or runtime enforcement.',
})

apk_old,apk_new = ROOT/'muse-from-meta-8-0-0-21-168.apk',W/'Muse-android-9-candidate.apk'
android={}
permissions={}
for label,apk in [('baseline',apk_old),('current',apk_new)]:
    sig=run([a.build_tools/'apksigner','verify','--verbose','--print-certs',apk]); assert sig['exit_code']==0
    badging=subprocess.check_output([str(a.build_tools/'aapt2'),'dump','badging',str(apk)]).decode()
    permissions[label]=sorted(re.findall(r"^uses-permission[^\n]+",badging,re.M))
    with zipfile.ZipFile(apk) as z:
        dexes={n:hashlib.sha256(z.read(n)).hexdigest() for n in sorted(z.namelist()) if re.fullmatch(r'classes\d*\.dex',n)}
    android[label]={'apk_sha256':sha(apk),'bytes':apk.stat().st_size,'badging_header':badging.splitlines()[:3],
        'signature':sig,'permissions':permissions[label],'dex_sha256':dexes}
    android[label]['signer_sha256']=re.search(r'Signer #1 certificate SHA-256 digest: ([a-f0-9]+)',sig['output'])[1]
oldsrc=ROOT/'extracted-apk/jadx/sources/com/facebook/aura';newsrc=W/'android-jadx/sources/com/facebook/aura'
oa={str(f.relative_to(oldsrc)) for f in oldsrc.rglob('*.java')};na={str(f.relative_to(newsrc)) for f in newsrc.rglob('*.java')}
focus=('permissions/','skills/repo/Task','skills/repo/Recipient','common/prefs/HatchDeveloper','nodes/datasource/Proactive','commands/network/')
log=(W/'jadx.log').read_text()
errors=re.search(r'finished with errors, count: (\d+)',log)
write('03-android-comparison.json', {'samples':android,'signer_matches_baseline':android['baseline']['signer_sha256']==android['current']['signer_sha256'],
    'permissions_added':sorted(set(permissions['current'])-set(permissions['baseline'])),
    'permissions_removed':sorted(set(permissions['baseline'])-set(permissions['current'])),
    'new_named_classes_selected':sorted(x for x in na-oa if x.startswith(focus) and '$' not in x),
    'jadx_version':run(['jadx','--version'])['output'],'jadx_errors':int(errors[1]) if errors else None,
    'limits':'JADX reconstruction errors are not app exceptions. Selected important branches were checked in DEX disassembly; runtime defaults/uploads and Play-store trust anchoring remain untested.'})
for src,dst in [('extension-tests.json','04-extension-unit-tests.json'),('browser-tests.json','05-extension-browser-tests.json')]:
    result = json.loads((W/src).read_text())
    assert result['extension_version'] == json.loads((NEW/'Contents/Resources/chrome/manifest.json').read_text())['version']
    for name, digest in result.get('input_sha256', result.get('source_sha256', {})).items():
        assert extension_new[name] == digest, ('Test input does not match extracted extension', name)
    write(dst,result)

excerpts=[]
def excerpt(path,ranges):
    lines=path.read_text().splitlines()
    excerpts.append('\n## '+str(path.relative_to(ROOT))+'\nsha256: '+sha(path))
    for start,end in ranges:
        if not 1<=start<=end<=len(lines): raise ValueError((path,start,end))
        excerpts.extend(f'{i+1}: {lines[i]}'.rstrip() for i in range(start-1,end))
base=NEW/'Contents/Resources/chrome'
for rel,ranges in [
    ('lib/connection.js',[(34,85),(129,164),(200,235),(509,553)]),
    ('lib/events.js',[(8,60),(63,81)]),
    ('background.js',[(17,19),(293,303),(500,525),(549,570),(617,630)]),
]: excerpt(base/rel,ranges)
write('06-extension-excerpts.txt','# Unmodified extension excerpts; shipped with both Mac 3.0 and 4.1.\n'+'\n'.join(excerpts))

excerpts=[]
for rel,ranges in [
    ('commands/network/NetworkStateDataSource.java',[(23,32)]),
    ('gateway/AuraProactiveSyncManager.java',[(27,54),(104,111)]),
    ('permissions/defaults/PermissionDefaultMode.java',[(27,43)]),
]: excerpt(newsrc/rel,ranges)
excerpt(oldsrc/'commands/network/NetworkStateDataSource.java',[(26,34)])
smali=W/'android-smali'
for file,methods in [
    ('PermissionDefaultMode$Companion.smali',['fromWire']),
    ('HatchNodeHitlGate.smali',['resolveConnectorBaseline','ask']),
    ('NodeHitlCatalog.smali',['forDataSource']),
    ('NetworkStateDataSource.smali',['<clinit>']),
    ('AuraProactiveSyncWorker.smali',['doBackgroundWork']),
    ('ProactiveSyncRunner.smali',['run']),
]:
    source=next(smali.rglob(file));s=source.read_text()
    excerpts.append('\n## '+str(source.relative_to(ROOT))+'\nsha256: '+sha(source)+'\n# Blank/debug line directives omitted. File line numbers and DEX code-unit offsets retained.')
    for m in re.finditer(r'^\.method .*?^\.end method',s,re.M|re.S):
        if not any(re.search(r' '+re.escape(name)+r'\(',m[0].splitlines()[0]) for name in methods): continue
        start=s[:m.start()].count('\n')+1
        excerpts.extend(f'{start+i}: {line}' for i,line in enumerate(m[0].splitlines()) if line.strip() and not line.strip().startswith(('.line','.local','.end local','.restart local')))
write('07-android-bytecode-excerpts.txt','# Android 9.0.0.11.178: selected source and DEX evidence. Static, not execution.\n'+'\n'.join(excerpts))
print('Wrote 7 evidence files to '+str(OUT))
