def test_pack_unpack_roundtrip(self):
        pack = _testcapi.float_pack
        unpack = _testcapi.float_unpack

        large = 2.0 ** 100
        values = [1.0, 1.5, large, 1.0/7, math.pi]
        if HAVE_IEEE_754:
            values.extend((INF, NAN))
        for value in values:
            for size in (2, 4, 8,):
                if size == 2 and value == large:
                    # too large for 16-bit float
                    continue
                rel_tol = EPSILON[size]
                for endian in (BIG_ENDIAN, LITTLE_ENDIAN):
                    with self.subTest(value=value, size=size, endian=endian):
                        data = pack(size, value, endian)
                        value2 = unpack(data, endian)
                        if math.isnan(value):
                            self.assertTrue(math.isnan(value2), (value, value2))
                        elif size < 8:
                            self.assertTrue(math.isclose(value2, value, rel_tol=rel_tol),
                                            (value, value2))
                        else:
                            self.assertEqual(value2, value)