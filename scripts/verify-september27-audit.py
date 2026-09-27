#!/usr/bin/env python3
"""Read-only checks of the September 27 report's local artifacts; never runs Muse.

Uses macOS security and OpenSSL 3. Reads IPA members directly without publishing
FairPlay account metadata. Outputs only hashes, counts, signature results and
selected configuration. CMS verification uses Apple's local root, at the current
verification time; it does not contact revocation services.
"""
import base64
import hashlib
import json
from pathlib import Path
import plistlib
import struct
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'extracted/release-audit-2026-09-27'
OPENSSL = '/opt/homebrew/bin/openssl'
OUT = ROOT / 'evidence-updates/2026-09-27/09-independent-verification.json'
digest = lambda b: hashlib.sha256(b).hexdigest()


def run(args):
    return subprocess.run(list(map(str, args)), capture_output=True)


def b64(s):
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))


def macho_slices(b):
    if b[:4] == b'\xca\xfe\xba\xbe':
        return [struct.unpack_from('>II', b, 8 + i * 20 + 8)
                for i in range(struct.unpack_from('>I', b, 4)[0])]
    assert b[:4] in (b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe')
    return [(0, len(b))]


def commands(b, base):
    p = base + (32 if b[base:base+4] == b'\xcf\xfa\xed\xfe' else 28)
    for _ in range(struct.unpack_from('<I', b, base + 16)[0]):
        cmd, size = struct.unpack_from('<II', b, p)
        yield cmd, p, size
        p += size


def der_nodes(b, start=0, end=None):
    """Walk constructed DER nodes, retaining boundaries for attribute checks."""
    end = len(b) if end is None else end
    p = start
    while p < end:
        tag, ln = b[p], b[p+1]
        head = 2
        if ln & 128:
            n = ln & 127
            assert n and n <= 4
            ln = int.from_bytes(b[p+2:p+2+n], 'big'); head += n
        q = p + head; stop = q + ln
        assert stop <= end
        yield tag, b[q:stop], p, stop
        if tag & 32:
            yield from der_nodes(b, q, stop)
        p = stop
    assert p == end


def der_children(b):
    p = 0
    while p < len(b):
        node = next(der_nodes(b, p))
        yield node
        p = node[3]


with tempfile.TemporaryDirectory(prefix='muse-audit-verification-') as tmp:
    tmp = Path(tmp)
    result = {'audit_date': '2026-09-27', 'scope': 'Local cryptographic and byte/configuration checks; no native app execution or Meta account.',
              'openssl': run([OPENSSL, 'version']).stdout.decode().strip()}
    # Match all ordinary code hashes and verify each JWS signature with its
    # embedded certificate. Compare that certificate to the APK signer separately.
    apk = WORK / 'Muse-android-9-candidate.apk'
    android = {'apk_sha256': digest(apk.read_bytes()), 'jws': []}
    with zipfile.ZipFile(apk) as z:
        code = {n for n in z.namelist() if n.endswith('.so') or (n.startswith('classes') and n.endswith('.dex'))}
        for name in ['META-INF/code_transparency_signed.jwt', 'assets/fb_code_transparency_signed.jwt']:
            token = z.read(name).decode().strip(); head, body, sig = token.split('.')
            h, p = json.loads(b64(head)), json.loads(b64(body))
            assert h['alg'] == 'RS256'
            cert = base64.b64decode(h['x5c'][0])
            (tmp/'cert.der').write_bytes(cert)
            pub = run([OPENSSL, 'x509', '-inform', 'DER', '-in', tmp/'cert.der', '-pubkey', '-noout'])
            assert pub.returncode == 0
            (tmp/'pub.pem').write_bytes(pub.stdout)
            (tmp/'signed').write_bytes((head+'.'+body).encode())
            (tmp/'sig').write_bytes(b64(sig))
            verified = run([OPENSSL, 'dgst', '-sha256', '-verify', tmp/'pub.pem', '-signature', tmp/'sig', tmp/'signed'])
            assert verified.returncode == 0
            (tmp/'signed').write_bytes((head+'.'+body+'X').encode())
            rejected = run([OPENSSL, 'dgst', '-sha256', '-verify', tmp/'pub.pem', '-signature', tmp/'sig', tmp/'signed'])
            assert rejected.returncode != 0
            entries = p.get('codeRelatedFile', p.get('versions', [{}])[0].get('codeTransparencyRelatedFile', []))
            matched, special = [], []
            for entry in entries:
                path = entry.get('apkPath') or entry['path'].replace('base/dex/', '').removeprefix('base/')
                expected = entry.get('sha256', entry.get('digest'))
                if entry.get('type') == 'ANDROID_MANIFEST_V2':
                    special.append({'path': path, 'status': 'Not checked: custom canonical manifest digest, not a raw file SHA-256.'})
                    continue
                assert digest(z.read(path)) == expected, path
                matched.append(path)
            android['jws'].append({'member': name, 'sha256': digest(token.encode()), 'rs256_valid': True,
                                   'altered_message_rejected': True, 'certificate_sha256': digest(cert),
                                   'ordinary_file_hashes_matched': len(matched), 'all_dex_and_so_covered': code <= set(matched),
                                   'special_digests': special})
        android['code_files'] = len(code)
    signer = json.loads((ROOT/'evidence-updates/2026-09-27/03-android-comparison.json').read_text())['samples']['current']['signer_sha256']
    android['apk_signer_sha256'] = signer
    android['jws_certificates_match_apk_signer'] = all(j['certificate_sha256'] == signer for j in android['jws'])
    android['trust_limit'] = 'Embedded-certificate signature verification is not an independent trust anchor. The enclosing APK signature authenticates the packaged JWS; no separate official-store transparency-key comparison was performed.'
    result['android'] = android

    # Compare helper bytes outside declared signatures, retaining UUID changes.
    result['mac_helpers'] = []
    newapp = WORK/'Muse.app/Contents'; oldapp = ROOT/'extracted/Muse.app/Contents'
    for rel in ['Frameworks/Sparkle.framework/Versions/B/Sparkle',
                'Frameworks/Sparkle.framework/Versions/B/Autoupdate',
                'Frameworks/Sparkle.framework/Versions/B/Updater.app/Contents/MacOS/Updater',
                'Helpers/EndoCrashpadHandler']:
        if not (newapp/rel).exists():
            candidates = list(newapp.rglob(Path(rel).name))
            assert len(candidates) == 1, (rel, candidates)
            rel = str(candidates[0].relative_to(newapp))
        a, b = (oldapp/rel).read_bytes(), (newapp/rel).read_bytes()
        assert len(a) == len(b)
        sigmask, uuidmask = set(), set()
        for data in (a, b):
            for base, _ in macho_slices(data):
                for cmd, p, size in commands(data, base):
                    if cmd == 0x1d:
                        off, length = struct.unpack_from('<II', data, p+8)
                        sigmask.update(range(base+off, base+off+length))
                    if cmd == 0x1b: uuidmask.update(range(p+8, p+24))
        diffs = [i for i, (x, y) in enumerate(zip(a, b)) if x != y and i not in sigmask]
        result['mac_helpers'].append({'path': rel, 'baseline_sha256': digest(a), 'current_sha256': digest(b),
                                      'changed_bytes_outside_signature': len(diffs),
                                      'changed_bytes_outside_signature_and_uuid': len(set(diffs)-uuidmask)})
    spark = plistlib.loads((newapp/'Frameworks/Sparkle.framework/Versions/B/Resources/Info.plist').read_bytes())
    result['sparkle'] = {k: spark[k] for k in ['CFBundleShortVersionString', 'CFBundleVersion']}
    result['sparkle']['xpc_services'] = [str(p.relative_to(newapp)) for p in newapp.rglob('*.xpc')]

    # Verify primary CMS content and the signed SHA-256 CodeDirectory attribute;
    # then verify page hashes (normalizing only cryptid) and sealed special slots.
    root = run(['security', 'find-certificate', '-a', '-c', 'Apple Root CA', '-p', '/System/Library/Keychains/SystemRootCertificates.keychain'])
    assert root.returncode == 0
    (tmp/'apple.pem').write_bytes(root.stdout)
    ios = {'ipa_sha256': digest((ROOT/'com.facebook.hatch_8.1_und3fined.ipa').read_bytes()), 'binaries': []}
    with zipfile.ZipFile(ROOT/'com.facebook.hatch_8.1_und3fined.ipa') as z:
        inf = plistlib.loads(z.read('Payload/HatchApp.app/Info.plist'))
        ios['background_modes'] = inf.get('UIBackgroundModes', [])
        ios['permitted_bg_identifiers'] = inf.get('BGTaskSchedulerPermittedIdentifiers', [])
        for member in z.namelist():
            if member.endswith('/') or '/SC_Info/' in member: continue
            with z.open(member) as f: header = f.read(4)
            if header != b'\xcf\xfa\xed\xfe': continue
            data = z.read(member); normalized = bytearray(data); crypt = []
            for cmd, p, size in commands(data, 0):
                if cmd in (0x21, 0x2c):
                    off, length, cid = struct.unpack_from('<III', data, p+8)
                    crypt.append((off, length, cid))
                    if length and cid == 0: struct.pack_into('<I', normalized, p+16, 1)
                if cmd == 0x1d: sigoff, siglen = struct.unpack_from('<II', data, p+8)
            magic, length, count = struct.unpack_from('>III', data, sigoff)
            assert magic == 0xfade0cc0
            blobs = {}
            for i in range(count):
                slot, off = struct.unpack_from('>II', data, sigoff+12+8*i)
                blen = struct.unpack_from('>I', data, sigoff+off+4)[0]
                blobs[slot] = data[sigoff+off:sigoff+off+blen]
            (tmp/'cms.der').write_bytes(blobs[0x10000][8:]); (tmp/'primary.cd').write_bytes(blobs[0])
            verify = run([OPENSSL, 'cms', '-verify', '-binary', '-inform', 'DER', '-in', tmp/'cms.der',
                          '-content', tmp/'primary.cd', '-CAfile', tmp/'apple.pem', '-purpose', 'any', '-out', tmp/'cms-content'])
            assert verify.returncode == 0, (member, verify.stderr.decode())
            cd = blobs[0x1000] if 0x1000 in blobs else blobs[0]
            assert cd[37] == 2
            # Apple hash-agility-v2 OID 1.2.840.113635.100.9.2 lives inside
            # SignerInfo's authenticated attributes. Validate the typed digest pair.
            nodes = list(der_nodes(blobs[0x10000][8:]))
            signed_attributes = []
            for tag, value, _, _ in nodes:
                if tag != 0x30: continue
                fields = list(der_children(value))
                if len(fields) >= 6 and [x[0] for x in fields[:6]] == [0x02, 0x30, 0x30, 0xa0, 0x30, 0x04]:
                    signed_attributes.append(fields[3][1])
            assert len(signed_attributes) == 1
            attrs = [v for t, v, _, _ in der_children(signed_attributes[0])
                     if t == 0x30 and v.startswith(bytes.fromhex('06092a864886f763640902'))]
            assert len(attrs) == 1
            bound = bytes.fromhex('06096086480165030402010420') + hashlib.sha256(cd).digest()
            assert bound in attrs[0], 'SHA-256 CodeDirectory not bound in Apple agility attribute'
            # Negative control proves content-signature binding independently.
            bad = bytearray(blobs[0]); bad[-1] ^= 1; (tmp/'primary.cd').write_bytes(bad)
            tamper = run([OPENSSL, 'cms', '-verify', '-binary', '-inform', 'DER', '-in', tmp/'cms.der',
                          '-content', tmp/'primary.cd', '-CAfile', tmp/'apple.pem', '-purpose', 'any', '-out', tmp/'cms-content'])
            assert tamper.returncode != 0
            hash_offset, _, special_count, code_count, limit = struct.unpack_from('>IIIII', cd, 16)
            hash_size, hash_type, platform, page_bits = cd[36:40]
            assert hash_size == 32 and hash_type == 2
            page_size = 1 << page_bits
            mismatches = []
            for i in range(code_count):
                lo, hi = i*page_size, min((i+1)*page_size, limit)
                if hashlib.sha256(normalized[lo:hi]).digest() != cd[hash_offset+i*32:hash_offset+(i+1)*32]: mismatches.append(i)
            outside = [i for i in mismatches if not any(i*page_size < off+size and (i+1)*page_size > off for off,size,_ in crypt)]
            assert not outside, (member, outside)
            base = member.rsplit('/', 1)[0]
            seal = plistlib.loads(z.read(base+'/_CodeSignature/CodeResources'))
            resources_checked = 0
            resource_mismatches = []
            for rel, record in seal.get('files2', {}).items():
                if not isinstance(record, dict): continue
                if 'hash2' in record:
                    if hashlib.sha256(z.read(base+'/'+rel)).digest() == record['hash2']: resources_checked += 1
                    else: resource_mismatches.append(rel)
                elif 'hash' in record:
                    if hashlib.sha1(z.read(base+'/'+rel)).digest() == record['hash']: resources_checked += 1
                    else: resource_mismatches.append(rel)
            slots = {}
            for slot, raw in {1: z.read(base+'/Info.plist'), 2: blobs.get(2),
                              3: z.read(base+'/_CodeSignature/CodeResources'), 5: blobs.get(5), 7: blobs.get(7)}.items():
                if raw is None or slot > special_count: continue
                ok = hashlib.sha256(raw).digest() == cd[hash_offset-slot*32:hash_offset-(slot-1)*32]
                assert ok, (member, slot)
                slots[str(slot)] = ok
            ios['binaries'].append({'member': member, 'sha256': digest(data), 'cms_chain_to_apple_root_valid': True,
                'sha256_codedirectory_bound_by_signed_attribute': True, 'altered_primary_codedirectory_rejected': True,
                'code_pages': code_count, 'mismatched_pages_after_cryptid_normalization': len(mismatches),
                'mismatches_outside_fairplay_range': len(outside), 'special_slots_verified': slots,
                'resource_files_with_matching_sealed_hashes': resources_checked,
                'resource_hash_mismatches': resource_mismatches,
                'bytes_after_signature_region': len(data)-sigoff-siglen})
    ios['limit'] = 'Encrypted-range plaintext is unauthenticated. Signature-valid metadata and sealed resource hashes cannot authenticate decrypted instructions or establish retail runtime behavior. Omitted resources and account metadata were not authenticated or published.'
    result['ios'] = ios
    result['mac_native_input_sha256'] = digest((newapp/'MacOS/Muse').read_bytes())
    result['mac_native_rechecks'] = {}
    for label, address, count in [('auto_sync_resolver', '0x1001334bc', 75), ('crash_provider_enabled', '0x10064d288', 4)]:
        r = run(['xcrun', 'lldb', '--batch', '-o', f'target create "{newapp}/MacOS/Muse"',
                 '-o', f'disassemble --start-address {address} --count {count}'])
        assert r.returncode == 0
        result['mac_native_rechecks'][label] = r.stdout.decode().replace(str(ROOT), '<repo>')
    result['bounded_source_rechecks'] = []
    for relative, lo, hi in [
        ('Muse.app/Contents/Resources/chrome/background.js', 649, 680),
        ('android-jadx/sources/com/facebook/aura/commands/health/HealthDataSource.java', 335, 383),
        ('android-jadx/sources/com/facebook/aura/commands/sms/SmsDataSource.java', 208, 245),
    ]:
        source = WORK/relative
        lines = source.read_text().splitlines()
        assert hi <= len(lines)
        result['bounded_source_rechecks'].append({'file': relative, 'sha256': digest(source.read_bytes()),
            'lines': [f'{i+1}: {lines[i]}'.rstrip() for i in range(lo-1, hi)],
            'limit': 'JADX reconstructions are supporting static evidence, not execution. The extension JavaScript is original source.'})
    OUT.write_text(json.dumps(result, indent=2)+'\n')
    print('Wrote', OUT.relative_to(ROOT))
