def test_long_asnativebytes_fuzz(self):
        import math
        from random import Random
        from _testcapi import (
            pylong_asnativebytes as asnativebytes,
            SIZE_MAX,
        )

        # Abbreviate sizeof(Py_ssize_t) to SZ because we use it a lot
        SZ = int(math.ceil(math.log(SIZE_MAX + 1) / math.log(2)) / 8)

        rng = Random()
        # Allocate bigger buffer than actual values are going to be
        buffer = bytearray(260)

        for _ in range(1000):
            n = rng.randrange(1, 256)
            bytes_be = bytes([
                # Ensure the most significant byte is nonzero
                rng.randrange(1, 256),
                *[rng.randrange(256) for _ in range(n - 1)]
            ])
            bytes_le = bytes_be[::-1]
            v = int.from_bytes(bytes_le, 'little')

            expect_1 = expect_2 = (SZ, n)
            if bytes_be[0] & 0x80:
                # All values are positive, so if MSB is set, expect extra bit
                # when we request the size or have a large enough buffer
                expect_1 = (SZ, n + 1)
                # When passing Py_ASNATIVEBYTES_UNSIGNED_BUFFER, we expect the
                # return to be exactly the right size.
                expect_2 = (n,)

            try:
                actual = asnativebytes(v, buffer, 0, -1)
                self.assertIn(actual, expect_1)

                actual = asnativebytes(v, buffer, len(buffer), 0)
                self.assertIn(actual, expect_1)
                self.assertEqual(bytes_be, buffer[-n:])

                actual = asnativebytes(v, buffer, len(buffer), 1)
                self.assertIn(actual, expect_1)
                self.assertEqual(bytes_le, buffer[:n])

                actual = asnativebytes(v, buffer, n, 4)
                self.assertIn(actual, expect_2, bytes_be.hex())
                actual = asnativebytes(v, buffer, n, 5)
                self.assertIn(actual, expect_2, bytes_be.hex())
            except AssertionError as ex:
                value_hex = ''.join(reversed([
                    f'{b:02X}{"" if i % 8 else "_"}'
                    for i, b in enumerate(bytes_le, start=1)
                ])).strip('_')
                if support.verbose:
                    print()
                    print(n, 'bytes')
                    print('hex =', value_hex)
                    print('int =', v)
                    raise
                raise AssertionError(f"Value: 0x{value_hex}") from ex