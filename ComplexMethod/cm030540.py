def test_half_float(self):
        _testcapi = import_helper.import_module('_testcapi')
        # Little-endian examples from:
        # http://en.wikipedia.org/wiki/Half_precision_floating-point_format
        format_bits_float__cleanRoundtrip_list = [
            (b'\x00\x3c', 1.0),
            (b'\x00\xc0', -2.0),
            (b'\xff\x7b', 65504.0), #  (max half precision)
            (b'\x00\x04', 2**-14), # ~= 6.10352 * 10**-5 (min pos normal)
            (b'\x01\x00', 2**-24), # ~= 5.96046 * 10**-8 (min pos subnormal)
            (b'\x00\x00', 0.0),
            (b'\x00\x80', -0.0),
            (b'\x00\x7c', float('+inf')),
            (b'\x00\xfc', float('-inf')),
            (b'\x55\x35', 0.333251953125), # ~= 1/3
        ]

        for le_bits, f in format_bits_float__cleanRoundtrip_list:
            be_bits = le_bits[::-1]
            self.assertEqual(f, struct.unpack('<e', le_bits)[0])
            self.assertEqual(le_bits, struct.pack('<e', f))
            self.assertEqual(f, struct.unpack('>e', be_bits)[0])
            self.assertEqual(be_bits, struct.pack('>e', f))
            if sys.byteorder == 'little':
                self.assertEqual(f, struct.unpack('e', le_bits)[0])
                self.assertEqual(le_bits, struct.pack('e', f))
            else:
                self.assertEqual(f, struct.unpack('e', be_bits)[0])
                self.assertEqual(be_bits, struct.pack('e', f))

        # Check for NaN handling:
        format_bits__nan_list = [
            ('<e', b'\x01\xfc'),
            ('<e', b'\x00\xfe'),
            ('<e', b'\xff\xff'),
            ('<e', b'\x01\x7c'),
            ('<e', b'\x00\x7e'),
            ('<e', b'\xff\x7f'),
        ]

        for formatcode, bits in format_bits__nan_list:
            self.assertTrue(math.isnan(struct.unpack('<e', bits)[0]))
            self.assertTrue(math.isnan(struct.unpack('>e', bits[::-1])[0]))

        # Check that packing produces a bit pattern representing a quiet NaN:
        # all exponent bits and the msb of the fraction should all be 1.
        if _testcapi.nan_msb_is_signaling:
            # HP PA RISC and some MIPS CPUs use 0 for quiet, see:
            # https://en.wikipedia.org/wiki/NaN#Encoding
            expected = 0x7c
        else:
            expected = 0x7e

        packed = struct.pack('<e', math.nan)
        self.assertEqual(packed[1] & 0x7e, expected)
        packed = struct.pack('<e', -math.nan)
        self.assertEqual(packed[1] & 0x7e, expected)

        # Checks for round-to-even behavior
        format_bits_float__rounding_list = [
            ('>e', b'\x00\x01', 2.0**-25 + 2.0**-35), # Rounds to minimum subnormal
            ('>e', b'\x00\x00', 2.0**-25), # Underflows to zero (nearest even mode)
            ('>e', b'\x00\x00', 2.0**-26), # Underflows to zero
            ('>e', b'\x03\xff', 2.0**-14 - 2.0**-24), # Largest subnormal.
            ('>e', b'\x03\xff', 2.0**-14 - 2.0**-25 - 2.0**-65),
            ('>e', b'\x04\x00', 2.0**-14 - 2.0**-25),
            ('>e', b'\x04\x00', 2.0**-14), # Smallest normal.
            ('>e', b'\x3c\x01', 1.0+2.0**-11 + 2.0**-16), # rounds to 1.0+2**(-10)
            ('>e', b'\x3c\x00', 1.0+2.0**-11), # rounds to 1.0 (nearest even mode)
            ('>e', b'\x3c\x00', 1.0+2.0**-12), # rounds to 1.0
            ('>e', b'\x7b\xff', 65504), # largest normal
            ('>e', b'\x7b\xff', 65519), # rounds to 65504
            ('>e', b'\x80\x01', -2.0**-25 - 2.0**-35), # Rounds to minimum subnormal
            ('>e', b'\x80\x00', -2.0**-25), # Underflows to zero (nearest even mode)
            ('>e', b'\x80\x00', -2.0**-26), # Underflows to zero
            ('>e', b'\xbc\x01', -1.0-2.0**-11 - 2.0**-16), # rounds to 1.0+2**(-10)
            ('>e', b'\xbc\x00', -1.0-2.0**-11), # rounds to 1.0 (nearest even mode)
            ('>e', b'\xbc\x00', -1.0-2.0**-12), # rounds to 1.0
            ('>e', b'\xfb\xff', -65519), # rounds to 65504
        ]

        for formatcode, bits, f in format_bits_float__rounding_list:
            self.assertEqual(bits, struct.pack(formatcode, f))

        # This overflows, and so raises an error
        format_bits_float__roundingError_list = [
            # Values that round to infinity.
            ('>e', 65520.0),
            ('>e', 65536.0),
            ('>e', 1e300),
            ('>e', -65520.0),
            ('>e', -65536.0),
            ('>e', -1e300),
            ('<e', 65520.0),
            ('<e', 65536.0),
            ('<e', 1e300),
            ('<e', -65520.0),
            ('<e', -65536.0),
            ('<e', -1e300),
        ]

        for formatcode, f in format_bits_float__roundingError_list:
            self.assertRaises(OverflowError, struct.pack, formatcode, f)

        # Double rounding
        format_bits_float__doubleRoundingError_list = [
            ('>e', b'\x67\xff', 0x1ffdffffff * 2**-26), # should be 2047, if double-rounded 64>32>16, becomes 2048
        ]

        for formatcode, bits, f in format_bits_float__doubleRoundingError_list:
            self.assertEqual(bits, struct.pack(formatcode, f))