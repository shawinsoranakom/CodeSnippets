def test_one(self, x, pack=struct.pack,
                                  unpack=struct.unpack,
                                  unhexlify=binascii.unhexlify):

                format = self.format
                if self.min_value <= x <= self.max_value:
                    expected = x
                    if self.signed and x < 0:
                        expected += 1 << self.bitsize
                    self.assertGreaterEqual(expected, 0)
                    expected = '%x' % expected
                    if len(expected) & 1:
                        expected = "0" + expected
                    expected = expected.encode('ascii')
                    expected = unhexlify(expected)
                    expected = (b"\x00" * (self.bytesize - len(expected)) +
                                expected)
                    if (self.byteorder == '<' or
                        self.byteorder in ('', '@', '=') and not ISBIGENDIAN):
                        expected = string_reverse(expected)
                    self.assertEqual(len(expected), self.bytesize)

                    # Pack work?
                    got = pack(format, x)
                    self.assertEqual(got, expected)

                    # Unpack work?
                    retrieved = unpack(format, got)[0]
                    self.assertEqual(x, retrieved)

                    # Adding any byte should cause a "too big" error.
                    self.assertRaises((struct.error, TypeError), unpack, format,
                                                                 b'\x01' + got)
                else:
                    # x is out of range -- verify pack realizes that.
                    self.assertRaises((OverflowError, ValueError, struct.error),
                                      pack, format, x)