def test_ascii85_valid(self):
        # Test Ascii85 with valid data
        ASCII85_PREFIX = b"<~"
        ASCII85_SUFFIX = b"~>"

        # Interleave blocks of 4 null bytes and 4 spaces into test data
        rawdata = bytearray()
        rawlines, i = [], 0
        for k in range(1, len(self.rawdata) + 1):
            b = b"\0\0\0\0" if k & 1 else b"    "
            b = b + self.rawdata[i:i + k]
            b = b"    " if k & 1 else b"\0\0\0\0"
            rawdata += b
            rawlines.append(b)
            i += k
            if i >= len(self.rawdata):
                break

        # Test core parameter combinations
        params = (False, False), (False, True), (True, False), (True, True)
        for foldspaces, adobe in params:
            lines = []
            for rawline in rawlines:
                b = self.type2test(rawline)
                a = binascii.b2a_ascii85(b, foldspaces=foldspaces, adobe=adobe)
                lines.append(a)
            res = bytearray()
            for line in lines:
                a = self.type2test(line)
                b = binascii.a2b_ascii85(a, foldspaces=foldspaces, adobe=adobe)
                res += b
            self.assertEqual(res, rawdata)

        # Test decoding inputs with length 1 mod 5
        params = [
            (b"a", False, False, b"", b""),
            (b"xbw", False, False, b"wx", b""),
            (b"<~c~>", False, True, b"", b""),
            (b"{d ~>", False, True, b" {", b""),
            (b"ye", True, False, b"", b"    "),
            (b"z\x01y\x00f", True, False, b"\x00\x01", b"\x00\x00\x00\x00    "),
            (b"<~FCfN8yg~>", True, True, b"", b"test    "),
            (b"FE;\x03#8zFCf\x02N8yh~>", True, True, b"\x02\x03", b"tset\x00\x00\x00\x00test    "),
        ]
        for a, foldspaces, adobe, ignorechars, b in params:
            kwargs = {"foldspaces": foldspaces, "adobe": adobe, "ignorechars": ignorechars}
            self.assertEqual(binascii.a2b_ascii85(self.type2test(a), **kwargs), b)