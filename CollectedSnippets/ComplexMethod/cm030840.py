def test_fromhex(self):
        self.assertRaises(TypeError, self.type2test.fromhex)
        self.assertRaises(TypeError, self.type2test.fromhex, 1)
        self.assertEqual(self.type2test.fromhex(''), self.type2test())
        b = bytearray([0x1a, 0x2b, 0x30])
        self.assertEqual(self.type2test.fromhex('1a2B30'), b)
        self.assertEqual(self.type2test.fromhex('  1A 2B  30   '), b)

        # check that ASCII whitespace is ignored
        self.assertEqual(self.type2test.fromhex(' 1A\n2B\t30\v'), b)
        self.assertEqual(self.type2test.fromhex(b' 1A\n2B\t30\v'), b)
        for c in "\x09\x0A\x0B\x0C\x0D\x20":
            self.assertEqual(self.type2test.fromhex(c), self.type2test())
        for c in "\x1C\x1D\x1E\x1F\x85\xa0\u2000\u2002\u2028":
            self.assertRaises(ValueError, self.type2test.fromhex, c)

        # Check that we can parse bytes and bytearray
        tests = [
            ("bytes", bytes),
            ("bytearray", bytearray),
            ("memoryview", memoryview),
            ("array.array", lambda bs: array.array('B', bs)),
        ]
        for name, factory in tests:
            with self.subTest(name=name):
                self.assertEqual(self.type2test.fromhex(factory(b' 1A 2B 30 ')), b)

        # Invalid bytes are rejected
        for u8 in b"\0\x1C\x1D\x1E\x1F\x85\xa0":
            b = bytes([30, 31, u8])
            self.assertRaises(ValueError, self.type2test.fromhex, b)

        self.assertEqual(self.type2test.fromhex('0000'), b'\0\0')
        with self.assertRaisesRegex(
            TypeError,
            r'fromhex\(\) argument must be str or bytes-like, not tuple',
        ):
            self.type2test.fromhex(())
        self.assertRaises(ValueError, self.type2test.fromhex, 'a')
        self.assertRaises(ValueError, self.type2test.fromhex, 'rt')
        self.assertRaises(ValueError, self.type2test.fromhex, '1a b cd')
        self.assertRaises(ValueError, self.type2test.fromhex, '\x00')
        self.assertRaises(ValueError, self.type2test.fromhex, '12   \x00   34')

        # For odd number of character(s)
        for value in ("a", "aaa", "deadbee"):
            with self.assertRaises(ValueError) as cm:
                self.type2test.fromhex(value)
            self.assertIn("fromhex() arg must contain an even number of hexadecimal digits", str(cm.exception))
        for value, position in (("a ", 1), (" aa a ", 5), (" aa a a ", 5)):
            with self.assertRaises(ValueError) as cm:
                self.type2test.fromhex(value)
            self.assertIn(f"non-hexadecimal number found in fromhex() arg at position {position}", str(cm.exception))

        for data, pos in (
            # invalid first hexadecimal character
            ('12 x4 56', 3),
            # invalid second hexadecimal character
            ('12 3x 56', 4),
            # two invalid hexadecimal characters
            ('12 xy 56', 3),
            # test non-ASCII string
            ('12 3\xff 56', 4),
        ):
            with self.assertRaises(ValueError) as cm:
                self.type2test.fromhex(data)
            self.assertIn('at position %s' % pos, str(cm.exception))