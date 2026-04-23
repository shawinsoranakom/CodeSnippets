def test_codecs(self):
        # Encoding
        self.assertEqual('hello'.encode('ascii'), b'hello')
        self.assertEqual('hello'.encode('utf-7'), b'hello')
        self.assertEqual('hello'.encode('utf-8'), b'hello')
        self.assertEqual('hello'.encode('utf-8'), b'hello')
        self.assertEqual('hello'.encode('utf-16-le'), b'h\000e\000l\000l\000o\000')
        self.assertEqual('hello'.encode('utf-16-be'), b'\000h\000e\000l\000l\000o')
        self.assertEqual('hello'.encode('latin-1'), b'hello')

        # Default encoding is utf-8
        self.assertEqual('\u2603'.encode(), b'\xe2\x98\x83')

        # Roundtrip safety for BMP (just the first 1024 chars)
        for c in range(1024):
            u = chr(c)
            for encoding in ('utf-7', 'utf-8', 'utf-16', 'utf-16-le',
                             'utf-16-be', 'raw_unicode_escape',
                             'unicode_escape'):
                self.assertEqual(str(u.encode(encoding),encoding), u)

        # Roundtrip safety for BMP (just the first 256 chars)
        for c in range(256):
            u = chr(c)
            for encoding in ('latin-1',):
                self.assertEqual(str(u.encode(encoding),encoding), u)

        # Roundtrip safety for BMP (just the first 128 chars)
        for c in range(128):
            u = chr(c)
            for encoding in ('ascii',):
                self.assertEqual(str(u.encode(encoding),encoding), u)

        # Roundtrip safety for non-BMP (just a few chars)
        with warnings.catch_warnings():
            u = '\U00010001\U00020002\U00030003\U00040004\U00050005'
            for encoding in ('utf-8', 'utf-16', 'utf-16-le', 'utf-16-be',
                             'raw_unicode_escape', 'unicode_escape'):
                self.assertEqual(str(u.encode(encoding),encoding), u)

        # UTF-8 must be roundtrip safe for all code points
        # (except surrogates, which are forbidden).
        u = ''.join(map(chr, list(range(0, 0xd800)) +
                             list(range(0xe000, 0x110000))))
        for encoding in ('utf-8',):
            self.assertEqual(str(u.encode(encoding),encoding), u)