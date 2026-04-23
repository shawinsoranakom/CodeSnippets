def test_locale_flag(self):
        enc = locale.getpreferredencoding()
        # Search non-ASCII letter
        for i in range(128, 256):
            try:
                c = bytes([i]).decode(enc)
                sletter = c.lower()
                if sletter == c: continue
                bletter = sletter.encode(enc)
                if len(bletter) != 1: continue
                if bletter.decode(enc) != sletter: continue
                bpat = re.escape(bytes([i]))
                break
            except (UnicodeError, TypeError):
                pass
        else:
            bletter = None
            bpat = b'A'
        # Bytes patterns
        pat = re.compile(bpat, re.LOCALE | re.IGNORECASE)
        if bletter:
            self.assertTrue(pat.match(bletter))
        pat = re.compile(b'(?L)' + bpat, re.IGNORECASE)
        if bletter:
            self.assertTrue(pat.match(bletter))
        pat = re.compile(bpat, re.IGNORECASE)
        if bletter:
            self.assertIsNone(pat.match(bletter))
        pat = re.compile(br'\w', re.LOCALE)
        if bletter:
            self.assertTrue(pat.match(bletter))
        pat = re.compile(br'(?L)\w')
        if bletter:
            self.assertTrue(pat.match(bletter))
        pat = re.compile(br'\w')
        if bletter:
            self.assertIsNone(pat.match(bletter))
        # Incompatibilities
        self.assertRaises(ValueError, re.compile, '', re.LOCALE)
        self.assertRaises(re.PatternError, re.compile, '(?L)')
        self.assertRaises(ValueError, re.compile, b'', re.LOCALE | re.ASCII)
        self.assertRaises(ValueError, re.compile, b'(?L)', re.ASCII)
        self.assertRaises(ValueError, re.compile, b'(?a)', re.LOCALE)
        self.assertRaises(re.PatternError, re.compile, b'(?aL)')