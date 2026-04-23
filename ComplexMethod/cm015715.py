def testRemainder(self):
        from fractions import Fraction

        def validate_spec(x, y, r):
            """
            Check that r matches remainder(x, y) according to the IEEE 754
            specification. Assumes that x, y and r are finite and y is nonzero.
            """
            fx, fy, fr = Fraction(x), Fraction(y), Fraction(r)
            # r should not exceed y/2 in absolute value
            self.assertLessEqual(abs(fr), abs(fy/2))
            # x - r should be an exact integer multiple of y
            n = (fx - fr) / fy
            self.assertEqual(n, int(n))
            if abs(fr) == abs(fy/2):
                # If |r| == |y/2|, n should be even.
                self.assertEqual(n/2, int(n/2))

        # triples (x, y, remainder(x, y)) in hexadecimal form.
        testcases = [
            # Remainders modulo 1, showing the ties-to-even behaviour.
            '-4.0 1 -0.0',
            '-3.8 1  0.8',
            '-3.0 1 -0.0',
            '-2.8 1 -0.8',
            '-2.0 1 -0.0',
            '-1.8 1  0.8',
            '-1.0 1 -0.0',
            '-0.8 1 -0.8',
            '-0.0 1 -0.0',
            ' 0.0 1  0.0',
            ' 0.8 1  0.8',
            ' 1.0 1  0.0',
            ' 1.8 1 -0.8',
            ' 2.0 1  0.0',
            ' 2.8 1  0.8',
            ' 3.0 1  0.0',
            ' 3.8 1 -0.8',
            ' 4.0 1  0.0',

            # Reductions modulo 2*pi
            '0x0.0p+0 0x1.921fb54442d18p+2 0x0.0p+0',
            '0x1.921fb54442d18p+0 0x1.921fb54442d18p+2  0x1.921fb54442d18p+0',
            '0x1.921fb54442d17p+1 0x1.921fb54442d18p+2  0x1.921fb54442d17p+1',
            '0x1.921fb54442d18p+1 0x1.921fb54442d18p+2  0x1.921fb54442d18p+1',
            '0x1.921fb54442d19p+1 0x1.921fb54442d18p+2 -0x1.921fb54442d17p+1',
            '0x1.921fb54442d17p+2 0x1.921fb54442d18p+2 -0x0.0000000000001p+2',
            '0x1.921fb54442d18p+2 0x1.921fb54442d18p+2  0x0p0',
            '0x1.921fb54442d19p+2 0x1.921fb54442d18p+2  0x0.0000000000001p+2',
            '0x1.2d97c7f3321d1p+3 0x1.921fb54442d18p+2  0x1.921fb54442d14p+1',
            '0x1.2d97c7f3321d2p+3 0x1.921fb54442d18p+2 -0x1.921fb54442d18p+1',
            '0x1.2d97c7f3321d3p+3 0x1.921fb54442d18p+2 -0x1.921fb54442d14p+1',
            '0x1.921fb54442d17p+3 0x1.921fb54442d18p+2 -0x0.0000000000001p+3',
            '0x1.921fb54442d18p+3 0x1.921fb54442d18p+2  0x0p0',
            '0x1.921fb54442d19p+3 0x1.921fb54442d18p+2  0x0.0000000000001p+3',
            '0x1.f6a7a2955385dp+3 0x1.921fb54442d18p+2  0x1.921fb54442d14p+1',
            '0x1.f6a7a2955385ep+3 0x1.921fb54442d18p+2  0x1.921fb54442d18p+1',
            '0x1.f6a7a2955385fp+3 0x1.921fb54442d18p+2 -0x1.921fb54442d14p+1',
            '0x1.1475cc9eedf00p+5 0x1.921fb54442d18p+2  0x1.921fb54442d10p+1',
            '0x1.1475cc9eedf01p+5 0x1.921fb54442d18p+2 -0x1.921fb54442d10p+1',

            # Symmetry with respect to signs.
            ' 1  0.c  0.4',
            '-1  0.c -0.4',
            ' 1 -0.c  0.4',
            '-1 -0.c -0.4',
            ' 1.4  0.c -0.4',
            '-1.4  0.c  0.4',
            ' 1.4 -0.c -0.4',
            '-1.4 -0.c  0.4',

            # Huge modulus, to check that the underlying algorithm doesn't
            # rely on 2.0 * modulus being representable.
            '0x1.dp+1023 0x1.4p+1023  0x0.9p+1023',
            '0x1.ep+1023 0x1.4p+1023 -0x0.ap+1023',
            '0x1.fp+1023 0x1.4p+1023 -0x0.9p+1023',
        ]

        for case in testcases:
            with self.subTest(case=case):
                x_hex, y_hex, expected_hex = case.split()
                x = float.fromhex(x_hex)
                y = float.fromhex(y_hex)
                expected = float.fromhex(expected_hex)
                validate_spec(x, y, expected)
                actual = math.remainder(x, y)
                # Cheap way of checking that the floats are
                # as identical as we need them to be.
                self.assertEqual(actual.hex(), expected.hex())

        # Test tiny subnormal modulus: there's potential for
        # getting the implementation wrong here (for example,
        # by assuming that modulus/2 is exactly representable).
        tiny = float.fromhex('1p-1074')  # min +ve subnormal
        for n in range(-25, 25):
            if n == 0:
                continue
            y = n * tiny
            for m in range(100):
                x = m * tiny
                actual = math.remainder(x, y)
                validate_spec(x, y, actual)
                actual = math.remainder(-x, y)
                validate_spec(-x, y, actual)

        # Special values.
        # NaNs should propagate as usual.
        for value in [NAN, 0.0, -0.0, 2.0, -2.3, NINF, INF]:
            self.assertIsNaN(math.remainder(NAN, value))
            self.assertIsNaN(math.remainder(value, NAN))

        # remainder(x, inf) is x, for non-nan non-infinite x.
        for value in [-2.3, -0.0, 0.0, 2.3]:
            self.assertEqual(math.remainder(value, INF), value)
            self.assertEqual(math.remainder(value, NINF), value)

        # remainder(x, 0) and remainder(infinity, x) for non-NaN x are invalid
        # operations according to IEEE 754-2008 7.2(f), and should raise.
        for value in [NINF, -2.3, -0.0, 0.0, 2.3, INF]:
            with self.assertRaises(ValueError):
                math.remainder(INF, value)
            with self.assertRaises(ValueError):
                math.remainder(NINF, value)
            with self.assertRaises(ValueError):
                math.remainder(value, 0.0)
            with self.assertRaises(ValueError):
                math.remainder(value, -0.0)