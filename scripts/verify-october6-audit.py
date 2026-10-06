#!/usr/bin/env python3
"""Verify saved October 6 packages without executing Muse or using an account.

Requires the saved archives in muse-v9/, extracted/v9/, the September 27
baseline, macOS command-line tools, OpenSSL 3 and Android build-tools 36.1.0.
Only hashes, metadata and bounded excerpts are published; no account metadata.
"""
import base64
from collections import Counter
import importlib.util
import json
from pathlib import Path
import plistlib
import re
import struct
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent
W = ROOT/'extracted/v9'
OLD = ROOT/'extracted/release-audit-2026-09-27'
PACKAGES = ROOT/'muse-v9'
BT = Path.home()/'Library/Android/sdk/build-tools/36.1.0'
spec = importlib.util.spec_from_file_location('previous_verifier', ROOT/'scripts/verify-september27-audit.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
sha = v.digest
APK = PACKAGES/'muse-from-meta-9-0-0-23-178.apk'
IPA = PACKAGES/'com.facebook.hatch_9.1_und3fined.ipa'
DMG = PACKAGES/'Muse-6.0.dmg'
OUT = ROOT/'evidence-updates/2026-10-06/11-independent-verification.json'


def command(args, expected=0):
    r = v.run(args)
    assert r.returncode == expected, (args, r.stderr.decode(errors='replace'))
    return {'exit_code': r.returncode, 'output': (r.stdout+r.stderr).decode(errors='replace').strip().replace(str(ROOT), '<repo>')}


def dylibs(b):
    names = []
    for cmd, p, size in v.commands(b, 0):
        if cmd in (0xc, 0x80000018, 0x8000001f, 0x20, 0x80000023):
            start = p+struct.unpack_from('<I', b, p+8)[0]
            names.append(b[start:b.index(b'\0', start, p+size)].decode())
    return sorted(names)


def snippet(path, needle, before=1, after=5):
    lines = path.read_text().splitlines()
    positions = [i for i, line in enumerate(lines) if needle in line]
    assert positions, (path, needle)
    i = positions[0]
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path.read_bytes()), 'needle': needle,
            'lines': [f'{j+1}: {lines[j]}' for j in range(max(0, i-before), min(len(lines), i+after+1))]}


def main():
    result = v.verify(apk=APK, ipa=IPA, oldapp=OLD/'Muse.app/Contents', newapp=W/'Muse.app/Contents',
                      audit_date='2026-10-06', source_rechecks=[], native_rechecks=(
                          ('proactive_sync_config_branch', '0x1001eb630', 71),
                          ('sparkle_launch_setters', '0x1000edd68', 17),
                          ('sparkle_true_argument_helper', '0x10069dacc', 3)))
    result['reviewed_commit'] = '3058622f65ce01b321a9159904f05dfee8e2e882'
    result['archives'] = {p.name: {'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size} for p in (APK, IPA, DMG)}
    mac = result['macos'] = {}
    infos, ents = {}, {}
    for label, app in [('baseline', OLD/'Muse.app'), ('current', W/'Muse.app')]:
        infos[label] = plistlib.loads((app/'Contents/Info.plist').read_bytes())
        ent = v.run(['codesign', '-d', '--entitlements', '-', '--xml', app]); assert ent.returncode == 0
        ents[label] = plistlib.loads(ent.stdout)
        mac[label] = {'version': infos[label]['CFBundleShortVersionString'], 'build': infos[label]['CFBundleVersion'],
                      'signature': command(['codesign', '--verify', '--deep', '--strict', app]),
                      'identity': command(['codesign', '-dvvv', app]),
                      'extension_file_count': sum(p.is_file() for p in (app/'Contents/Resources/chrome').rglob('*')),
                      'stealth_js_present': (app/'Contents/Resources/stealth.min.js').exists()}
    mac['entitlement_delta'] = {k: [ents['baseline'].get(k), ents['current'].get(k)] for k in sorted(set(ents['baseline'])|set(ents['current'])) if ents['baseline'].get(k)!=ents['current'].get(k)}
    mac['gatekeeper_assessment'] = command(['spctl', '-a', '-vvv', '-t', 'exec', W/'Muse.app'])
    feed = ET.parse(W/'appcast.xml'); ns = {'s': 'http://www.andymatuschak.org/xml-namespaces/sparkle'}
    item = feed.find('./channel/item'); enc = item.find('enclosure')
    assert item.findtext('s:shortVersionString', namespaces=ns) == infos['current']['CFBundleShortVersionString']
    assert int(enc.get('length')) == DMG.stat().st_size
    key = infos['baseline']['SUPublicEDKey']; assert key == infos['current']['SUPublicEDKey']
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t/'key').write_bytes(bytes.fromhex('302a300506032b6570032100')+base64.b64decode(key))
        (t/'sig').write_bytes(base64.b64decode(enc.get('{'+ns['s']+'}edSignature')))
        args = [v.OPENSSL, 'pkeyutl', '-verify', '-pubin', '-keyform', 'DER', '-inkey', t/'key', '-rawin', '-sigfile', t/'sig', '-in']
        assert v.run(args+[DMG]).returncode == 0
        b = bytearray(DMG.read_bytes()); b[len(b)//2] ^= 1; (t/'changed').write_bytes(b)
        assert v.run(args+[t/'changed']).returncode != 0
    mac['feed'] = {'source': infos['current']['SUFeedURL'], 'saved_feed_sha256': sha((W/'appcast.xml').read_bytes()), 'version': item.findtext('s:shortVersionString', namespaces=ns), 'published': item.findtext('pubDate'), 'ed25519_valid': True, 'changed_dmg_rejected': True, 'pinned_key': key}
    # Resolve chained-rebase selector targets; retain exact pointer bits and instruction evidence.
    b = (W/'Muse.app/Contents/MacOS/Muse').read_bytes()
    segments = [struct.unpack_from('<QQQQ', b, p+24) for c,p,_ in v.commands(b,0) if c == 0x19]
    def fileoff(addr):
        return next(f+addr-va for va,_,f,size in segments if va <= addr < va+size)
    mac['sparkle_setter_selectors'] = []
    for address in (0x10125a518, 0x10125a520):
        pointer = struct.unpack_from('<Q', b, fileoff(address))[0]
        offset = fileoff(pointer & 0xfffffffff)
        name = b[offset:b.index(b'\0', offset)].decode()
        assert name in ('setAutomaticallyChecksForUpdates:', 'setAutomaticallyDownloadsUpdates:')
        mac['sparkle_setter_selectors'].append({'selector_reference_va': hex(address), 'raw_pointer': hex(pointer), 'selector': name, 'argument': 'w2=1 via helper 0x10069dacc; see disassembly'})
    js = W/'prep/index60.main.pretty.js'
    mac['web_bundle_sha256'] = sha((W/'Muse.app/Contents/Resources/hatch/index.html').read_bytes())
    mac['web_excerpts'] = [snippet(js, needle, before, after) for needle,before,after in [
        ('function autoSyncBlock(',0,5), ('function localConnectorAutoSyncRowProps(',0,3),
        ('Wi?.autoSync.enabled ?? true',1,9), ('r.data?.trainingEnabled ?? true',9,6),
        ('getItem(CLIENT_TELEMETRY_ENABLED_KEY)',2,3)]]
    rawjs = (W/'Muse.app/Contents/Resources/hatch/index.html').read_text()
    mac['original_web_excerpts'] = []
    for needle, before, after in [('function autoSyncBlock(',0,320), ('function localConnectorAutoSyncRowProps(',0,220), ('Wi?.autoSync.enabled??!0',100,400), ('r.data?.trainingEnabled??!0',100,300)]:
        offset = rawjs.index(needle)
        mac['original_web_excerpts'].append({'needle': needle, 'character_offset': offset, 'excerpt': rawjs[max(0,offset-before):offset+after]})
    with tempfile.TemporaryDirectory() as td:
        invpath = Path(td)/'inventory.json'
        command(['python3', ROOT/'scripts/inventory-app.py', W/'Muse.app', invpath])
        rows = json.loads(invpath.read_text())
        mac['reviewed_inventory'] = {'entries': len(rows), 'seal_status': dict(Counter(r['seal'] for r in rows)),
            'parse_errors_or_unsupported': [{'path': r['path'], 'error': r['parse_error']} for r in rows if r.get('parse_error')],
            'trailing_bytes': [{'path': r['path'], 'bytes': r['trailing_bytes']} for r in rows if r.get('trailing_bytes')],
            'limit': 'Structural boundary checks are not proof that no hidden payload exists. JPEG is explicitly unverified.'}
    android = result['android']; permissions = {}; libs = {}
    for label, path in [('baseline', OLD/'Muse-android-9-candidate.apk'), ('current', APK)]:
        signed = command([BT/'apksigner', 'verify', '--verbose', '--print-certs', path])
        signer = re.search(r'Signer #1 certificate SHA-256 digest: (\w+)', signed['output']).group(1)
        assert signer == android['apk_signer_sha256']
        badging = command([BT/'aapt2', 'dump', 'badging', path])['output']
        permissions[label] = sorted(set(re.findall(r"^uses-permission[^\n]*name='([^']+)'", badging, re.M)))
        with zipfile.ZipFile(path) as z:
            libs[label] = {n: sha(z.read(n)) for n in z.namelist() if n.endswith('.so')}
            dex = [z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex', n)]
            android[label+'_photo_class_markers'] = sum(d.count(b'Lcom/facebook/aura/commands/photos/') for d in dex)
        android[label+'_verification'] = {'signature': signed, 'badging_package': badging.splitlines()[0], 'permission_count': len(permissions[label])}
    android['permission_delta'] = {'removed': sorted(set(permissions['baseline'])-set(permissions['current'])), 'added': sorted(set(permissions['current'])-set(permissions['baseline']))}
    android['native_libraries'] = {'count': len(libs['current']), 'maps_equal': libs['baseline']==libs['current'], 'current_sha256': libs['current']}
    src = W/'android-jadx/sources/com/facebook/aura'
    android['source_excerpts'] = [snippet(src/path, needle, before, after) for path,needle,before,after in [
        ('commands/network/NetworkStateHandlerKt.java','String ssid = wifiInfo.getSSID()',0,13),
        ('permissions/defaults/PermissionDefaultMode.java','AUTO_ALLOW :',3,2),
        ('permissions/defaults/PermissionDefaultsStore.java','public final void write(',0,10),
        ('gateway/HatchNodeHitlGate.java','public final Object resolveConnectorBaseline(',0,46),
        ('nodes/core/NodeHitlCatalog.java','public final NodeHitlSpec forDataSource(',0,54),
    ]]
    jar = Path('/opt/homebrew/Cellar/jadx/1.5.5/libexec/lib/jadx-1.5.5-all.jar')
    with tempfile.TemporaryDirectory() as td:
        command(['java', '-cp', jar, ROOT/'scripts/DisassembleSelected.java', APK, td, 'com.facebook.aura.commands.network.NetworkStateHandlerKt'])
        smali = list(Path(td).rglob('NetworkStateHandlerKt.smali')); assert len(smali) == 1
        lines = smali[0].read_text().splitlines()
        at = next(i for i,l in enumerate(lines) if l.startswith('.method ') and ' readWifi(' in l)
        end = next(i for i in range(at+1,len(lines)) if lines[i] == '.end method')
        android['wifi_permission_dex_excerpt'] = {'class': 'com.facebook.aura.commands.network.NetworkStateHandlerKt', 'apk_sha256': sha(APK.read_bytes()), 'smali_sha256': sha(smali[0].read_bytes()),
            'lines': [f'{j+1}: {lines[j]}' for j in range(at, end+1)]}
    ios = result['ios']; ios['delta'] = {}
    tokens = ['wss://shortwave.facebook.com/vllm_proxy', 'wss://shortwave.facebook.com/voyager/v1/asr/duplex', 'input_audio_buffer.append', 'HCHDeviceBLEManager', 'HCHMicroRecordingUploader', 'Muse Gadget', 'https://www.multimango.com/api/alo/default-models', 'NotesSyncSource', 'Apple Notes']
    oldipa = ROOT/'com.facebook.hatch_8.1_und3fined.ipa'
    dylib_sets = {}
    for label, path in [('baseline', oldipa), ('current', IPA)]:
        with zipfile.ZipFile(path) as z:
            b = z.read('Payload/HatchApp.app/HatchApp')
            info = plistlib.loads(z.read('Payload/HatchApp.app/Info.plist'))
            dylib_sets[label] = set(dylibs(b))
            ios['delta'][label] = {'binary_sha256': sha(b), 'version': info['CFBundleShortVersionString'], 'build': info['CFBundleVersion'], 'background_modes': info['UIBackgroundModes'], 'token_occurrences': {t: b.count(t.encode()) for t in tokens}, 'dylibs': sorted(dylib_sets[label])}
    ios['delta']['dylibs_added'] = sorted(dylib_sets['current']-dylib_sets['baseline'])
    ios['delta']['dylibs_removed'] = sorted(dylib_sets['baseline']-dylib_sets['current'])
    binary = W/'ipa/Payload/HatchApp.app/HatchApp'
    nm = command(['xcrun', 'nm', '-u', binary])['output']
    ids = sorted(set(re.findall(r'\b_HK\w*TypeIdentifier\w*', nm)))
    ios['health_identifier_imports'] = {'count': len(ids), 'identifiers': ids, 'limit': 'Imports do not establish permission grants, immediate-delivery execution or raw-sample transmission.'}
    result['limits'] = ['No native app execution, account session or production traffic capture.', 'Selected literal sets are not byte-identical command implementations.', 'Negative container/name searches cannot exclude all hidden behavior.', 'The preserved finder ledger contains interpretations superseded by the review.']
    OUT.write_text(json.dumps(result, indent=2)+'\n')
    print('Wrote', OUT.relative_to(ROOT))


if __name__ == '__main__':
    main()
