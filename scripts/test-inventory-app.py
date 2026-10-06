#!/usr/bin/env python3
"""Regression fixtures for cases that invalidated the original inventory claims."""
import importlib.util
from pathlib import Path
import struct
import unittest
import zlib

spec = importlib.util.spec_from_file_location('inventory', Path(__file__).with_name('inventory-app.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def chunk(kind, payload=b''):
    return struct.pack('>I', len(payload))+kind+payload+struct.pack('>I', zlib.crc32(kind+payload))


class StructuralChecks(unittest.TestCase):
    def test_png_embedded_iend_is_not_end(self):
        png = b'\x89PNG\r\n\x1a\n'+chunk(b'tEXt', b'comment\0IEND is data')+chunk(b'IEND')
        self.assertEqual(m.declared_end(png+b'payload'), (len(png), None))

    def test_png_crc_and_truncation(self):
        png = b'\x89PNG\r\n\x1a\n'+chunk(b'IEND')
        for bad in (png[:-1], png[:-1]+bytes([png[-1]^1])):
            self.assertIsNone(m.declared_end(bad)[0])
            self.assertIsNotNone(m.declared_end(bad)[1])

    def test_mp4_oversize_and_extended_header(self):
        for data in (struct.pack('>I4s', 100, b'ftyp'), struct.pack('>I4s',1,b'ftyp'), struct.pack('>I4sQ',1,b'ftyp',8)):
            self.assertIsNone(m.declared_end(data)[0])
            self.assertIsNotNone(m.declared_end(data)[1])

    def test_mp4_valid_tail(self):
        data = struct.pack('>I4s', 12, b'ftyp')+b'isom'
        self.assertEqual(m.declared_end(data+b'xyz'), (len(data), None))

    def test_macho_out_of_file_segment(self):
        header = struct.pack('<8I',0xfeedfacf,0,0,0,1,72,0,0)
        segment = struct.pack('<II16sQQQQIIII',25,72,b'__TEXT',0,200,0,200,0,0,0,0)
        self.assertIsNotNone(m.declared_end(header+segment)[1])

    def test_macho_invalid_command_length(self):
        header = struct.pack('<8I',0xfeedfacf,0,0,0,1,8,0,0)
        self.assertIsNotNone(m.declared_end(header+struct.pack('<II',25,0))[1])

    def test_fat_slice_beyond_eof(self):
        data=struct.pack('>II5I',0xcafebabe,1,0,0,28,999,0)
        self.assertIsNotNone(m.declared_end(data)[1])

    def test_jpeg_appended_fake_eoi_not_reported_clean(self):
        self.assertIsNone(m.declared_end(b'\xff\xd8\xff\xd9payload\xff\xd9')[0])
        self.assertIn('unsupported',m.declared_end(b'\xff\xd8\xff\xd9')[1])


if __name__ == '__main__':
    unittest.main()
