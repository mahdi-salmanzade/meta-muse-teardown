#!/usr/bin/env python3
"""Byte-level inventory of a macOS .app; never runs it.

For every file and symlink: SHA-256, size, `file` magic, Shannon entropy, whether its
bytes match a code-signature seal (every _CodeSignature/CodeResources in the bundle),
and, for Mach-O/MP4/PNG/JPEG, whether any bytes trail the format's declared end.

usage: inventory-app.py <App.app> <out.json>
"""
import hashlib, json, math, os, plistlib, re, struct, subprocess, sys
from collections import Counter

root, out = os.path.abspath(sys.argv[1]), sys.argv[2]


def entropy(b):
    if not b:
        return 0.0
    n = len(b)
    return -sum(v / n * math.log2(v / n) for v in Counter(b).values())


def magic(p):
    return subprocess.run(['file', '-b', p], capture_output=True, text=True).stdout.strip()


def mp4_end(b):
    pos = 0
    while pos + 8 <= len(b):
        size, kind = struct.unpack('>I4s', b[pos:pos + 8])
        if size == 1:
            size = struct.unpack('>Q', b[pos + 8:pos + 16])[0]
        elif size == 0:
            size = len(b) - pos
        if size < 8 or not re.match(rb'^[a-zA-Z0-9 _\xa9]{4}$', kind):
            return pos, f'bad box at {pos}'
        pos += size
    return pos, None


def macho_end(b):
    if struct.unpack('>I', b[:4])[0] == 0xcafebabe:
        n = struct.unpack('>I', b[4:8])[0]
        return max(off + size for _, _, off, size, _ in
                   (struct.unpack('>IIIII', b[8 + 20 * k:28 + 20 * k]) for k in range(n))), None
    if struct.unpack('<I', b[:4])[0] != 0xfeedfacf:
        return len(b), 'not thin 64-bit Mach-O'
    ncmds, sizeofcmds = struct.unpack('<II', b[16:24])
    off, end = 32, 32 + sizeofcmds
    for _ in range(ncmds):
        cmd, size = struct.unpack('<II', b[off:off + 8])
        if cmd == 0x19:  # LC_SEGMENT_64
            fileoff, filesize = struct.unpack('<QQ', b[off + 40:off + 56])
            end = max(end, fileoff + filesize)
        if cmd == 0x1d:  # LC_CODE_SIGNATURE
            dataoff, datasize = struct.unpack('<II', b[off + 8:off + 16])
            end = max(end, dataoff + datasize)
        off += size
    return end, None


def declared_end(b):
    if b[:4] in (b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe'):
        return macho_end(b)
    if b[4:8] == b'ftyp':
        return mp4_end(b)
    if b[:8] == b'\x89PNG\r\n\x1a\n':
        i = b.find(b'IEND')
        return (i + 8, None) if i >= 0 else (len(b), 'no IEND')
    if b[:3] == b'\xff\xd8\xff':
        i = b.rfind(b'\xff\xd9')
        return (i + 2, None) if i >= 0 else (len(b), 'no EOI')
    return None, None


# Map every sealed path to its expected digest, from every CodeResources in the bundle.
seals = {}
for dp, _, fn in os.walk(root):
    if os.path.basename(dp) == '_CodeSignature' and 'CodeResources' in fn:
        contents = os.path.dirname(dp)
        for rel, v in plistlib.load(open(os.path.join(dp, 'CodeResources'), 'rb')).get('files2', {}).items():
            full = os.path.normpath(os.path.join(contents, rel))
            if not isinstance(v, dict):
                seals[full] = ('sha1', v.hex())
            elif 'hash2' in v:
                seals[full] = ('file', v['hash2'].hex())
            elif 'symlink' in v:
                seals[full] = ('symlink', v['symlink'])
            elif 'cdhash' in v:
                seals[full] = ('nested', v['cdhash'].hex())

rows = []
for dp, dn, fn in os.walk(root):
    for name in sorted(fn) + [d for d in dn if os.path.islink(os.path.join(dp, d))]:
        p = os.path.join(dp, name)
        rel = os.path.relpath(p, root)
        s = seals.get(os.path.normpath(p))
        if os.path.islink(p):
            target = os.readlink(p)
            rows.append({'path': rel, 'type': 'symlink', 'target': target,
                         'seal': 'unsealed' if not s else ('ok' if s == ('symlink', target) else 'MISMATCH')})
            continue
        b = open(p, 'rb').read()
        h = hashlib.sha256(b).hexdigest()
        seal = 'unsealed' if s is None else (('ok' if s[1] == h else 'MISMATCH') if s[0] == 'file' else s[0])
        end, err = declared_end(b)
        rows.append({'path': rel, 'type': 'file', 'size': len(b), 'sha256': h, 'magic': magic(p)[:120],
                     'entropy': round(entropy(b), 3), 'seal': seal, 'declared_end': end,
                     'trailing_bytes': (len(b) - end) if end is not None else None, 'parse_error': err})

json.dump(rows, open(out, 'w'), indent=1)
print('entries:', len(rows), 'seal status:', dict(Counter(r['seal'] for r in rows)))
for r in rows:
    if r['seal'] == 'MISMATCH':
        print('SEAL MISMATCH', r['path'])
    if r.get('trailing_bytes'):
        print('TRAILING', r['trailing_bytes'], r['path'])
    if r.get('parse_error'):
        print('PARSE', r['parse_error'], r['path'])
