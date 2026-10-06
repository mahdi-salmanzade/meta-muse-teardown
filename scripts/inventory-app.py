#!/usr/bin/env python3
"""Byte-level inventory of a macOS .app; never runs it.

For every file and symlink: SHA-256, size, `file` magic, Shannon entropy, whether its
bytes match a code-signature seal (every _CodeSignature/CodeResources in the bundle),
and bounded structural-end checks for supported Mach-O/MP4/PNG files.
JPEG end detection is deliberately unsupported; a last-marker search is unsound.
Matching local seals is not signature-chain verification or proof of harmlessness.

usage: inventory-app.py <App.app> <out.json>
"""
import hashlib, json, math, os, plistlib, re, struct, subprocess, sys, zlib
from collections import Counter


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
        size, kind = struct.unpack_from('>I4s', b, pos)
        header = 8
        if size == 1:
            if pos + 16 > len(b):
                return None, f'truncated extended box at {pos}'
            size = struct.unpack_from('>Q', b, pos + 8)[0]
            header = 16
        elif size == 0:
            size = len(b) - pos
        if size < header or size > len(b) - pos:
            return None, f'invalid box length at {pos}'
        if not re.fullmatch(rb'[a-zA-Z0-9 _\xa9]{4}', kind):
            return None, f'unsupported box type at {pos}'
        pos += size
    return pos, None


def macho_end(b):
    if len(b) < 8:
        return None, 'truncated Mach-O header'
    if b[:4] == b'\xca\xfe\xba\xbe':
        n = struct.unpack_from('>I', b, 4)[0]
        if not n or 8 + 20 * n > len(b):
            return None, 'invalid fat architecture table'
        ends = []
        for k in range(n):
            _, _, off, size, _ = struct.unpack_from('>IIIII', b, 8 + 20 * k)
            if off < 8 + 20 * n or off + size > len(b):
                return None, 'fat slice outside file/table bounds'
            ends.append(off + size)
        return max(ends), None  # outer container only; gaps/slices not validated
    if len(b) < 32 or b[:4] != b'\xcf\xfa\xed\xfe':
        return None, 'unsupported or truncated thin Mach-O'
    ncmds, sizeofcmds = struct.unpack_from('<II', b, 16)
    off, end = 32, 32 + sizeofcmds
    if end > len(b):
        return None, 'load command table outside file'
    for _ in range(ncmds):
        if off + 8 > 32 + sizeofcmds:
            return None, 'truncated load command'
        cmd, size = struct.unpack_from('<II', b, off)
        if size < 8 or off + size > 32 + sizeofcmds:
            return None, 'invalid load command length'
        if cmd == 0x19:
            if size < 72:
                return None, 'truncated segment command'
            fileoff, filesize = struct.unpack_from('<QQ', b, off + 40)
            if filesize:
                end = max(end, fileoff + filesize)
        if cmd == 0x1d:
            if size < 16:
                return None, 'truncated signature command'
            dataoff, datasize = struct.unpack_from('<II', b, off + 8)
            end = max(end, dataoff + datasize)
        if end > len(b):
            return None, 'declared region outside file'
        off += size
    if off != 32 + sizeofcmds:
        return None, 'load command count/size mismatch'
    return end, None


def png_end(b):
    pos = 8
    while pos + 12 <= len(b):
        size = struct.unpack_from('>I', b, pos)[0]
        end = pos + 12 + size
        if end > len(b):
            return None, 'truncated PNG chunk'
        kind = b[pos + 4:pos + 8]
        crc = struct.unpack_from('>I', b, end - 4)[0]
        if zlib.crc32(b[pos + 4:end - 4]) != crc:
            return None, 'PNG chunk CRC mismatch'
        if kind == b'IEND':
            return (end, None) if size == 0 else (None, 'nonempty IEND')
        pos = end
    return None, 'missing or truncated IEND'


def declared_end(b):
    if b[:4] in (b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe'):
        return macho_end(b)
    if b[4:8] == b'ftyp':
        return mp4_end(b)
    if b[:8] == b'\x89PNG\r\n\x1a\n':
        return png_end(b)
    if b[:3] == b'\xff\xd8\xff':
        return None, 'JPEG structural parsing unsupported; no trailing-byte conclusion'
    return None, None


def main(root, out):
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
                elif 'hash' in v:
                    seals[full] = ('sha1', v['hash'].hex())
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
            seal = 'unsealed' if s is None else s[0]
            if s and s[0] in ('file', 'sha1'):
                actual = h if s[0] == 'file' else hashlib.sha1(b).hexdigest()
                seal = 'ok' if s[1] == actual else 'MISMATCH'
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


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]), sys.argv[2])
