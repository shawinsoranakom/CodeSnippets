def testFsum(self):
        # math.fsum relies on exact rounding for correct operation.
        # There's a known problem with IA32 floating-point that causes
        # inexact rounding in some situations, and will cause the
        # math.fsum tests below to fail; see issue #2937.  On non IEEE
        # 754 platforms, and on IEEE 754 platforms that exhibit the
        # problem described in issue #2937, we simply skip the whole
        # test.

        # Python version of math.fsum, for comparison.  Uses a
        # different algorithm based on frexp, ldexp and integer
        # arithmetic.
        from sys import float_info
        mant_dig = float_info.mant_dig
        etiny = float_info.min_exp - mant_dig

        def msum(iterable):
            """Full precision summation.  Compute sum(iterable) without any
            intermediate accumulation of error.  Based on the 'lsum' function
            at https://code.activestate.com/recipes/393090-binary-floating-point-summation-accurate-to-full-p/

            """
            tmant, texp = 0, 0
            for x in iterable:
                mant, exp = math.frexp(x)
                mant, exp = int(math.ldexp(mant, mant_dig)), exp - mant_dig
                if texp > exp:
                    tmant <<= texp-exp
                    texp = exp
                else:
                    mant <<= exp-texp
                tmant += mant
            # Round tmant * 2**texp to a float.  The original recipe
            # used float(str(tmant)) * 2.0**texp for this, but that's
            # a little unsafe because str -> float conversion can't be
            # relied upon to do correct rounding on all platforms.
            tail = max(len(bin(abs(tmant)))-2 - mant_dig, etiny - texp)
            if tail > 0:
                h = 1 << (tail-1)
                tmant = tmant // (2*h) + bool(tmant & h and tmant & 3*h-1)
                texp += tail
            return math.ldexp(tmant, texp)

        test_values = [
            ([], 0.0),
            ([0.0], 0.0),
            ([1e100, 1.0, -1e100, 1e-100, 1e50, -1.0, -1e50], 1e-100),
            ([1e100, 1.0, -1e100, 1e-100, 1e50, -1, -1e50], 1e-100),
            ([2.0**53, -0.5, -2.0**-54], 2.0**53-1.0),
            ([2.0**53, 1.0, 2.0**-100], 2.0**53+2.0),
            ([2.0**53+10.0, 1.0, 2.0**-100], 2.0**53+12.0),
            ([2.0**53-4.0, 0.5, 2.0**-54], 2.0**53-3.0),
            ([1./n for n in range(1, 1001)],
             float.fromhex('0x1.df11f45f4e61ap+2')),
            ([(-1.)**n/n for n in range(1, 1001)],
             float.fromhex('-0x1.62a2af1bd3624p-1')),
            ([1e16, 1., 1e-16], 10000000000000002.0),
            ([1e16-2., 1.-2.**-53, -(1e16-2.), -(1.-2.**-53)], 0.0),
            # exercise code for resizing partials array
            ([2.**n - 2.**(n+50) + 2.**(n+52) for n in range(-1074, 972, 2)] +
             [-2.**1022],
             float.fromhex('0x1.5555555555555p+970')),
            ]

        # Telescoping sum, with exact differences (due to Sterbenz)
        terms = [1.7**i for i in range(1001)]
        test_values.append((
            [terms[i+1] - terms[i] for i in range(1000)] + [-terms[1000]],
            -terms[0]
        ))

        for i, (vals, expected) in enumerate(test_values):
            try:
                actual = math.fsum(vals)
            except OverflowError:
                self.fail("test %d failed: got OverflowError, expected %r "
                          "for math.fsum(%.100r)" % (i, expected, vals))
            except ValueError:
                self.fail("test %d failed: got ValueError, expected %r "
                          "for math.fsum(%.100r)" % (i, expected, vals))
            self.assertEqual(actual, expected)

        from random import random, gauss, shuffle
        for j in range(1000):
            vals = [7, 1e100, -7, -1e100, -9e-20, 8e-20] * 10
            s = 0
            for i in range(200):
                v = gauss(0, random()) ** 7 - s
                s += v
                vals.append(v)
            shuffle(vals)

            s = msum(vals)
            self.assertEqual(msum(vals), math.fsum(vals))

        self.assertEqual(math.fsum([1.0, math.inf]), math.inf)
        self.assertTrue(math.isnan(math.fsum([math.nan, 1.0])))
        self.assertEqual(math.fsum([1e100, FloatLike(1.0), -1e100, 1e-100,
                                    1e50, FloatLike(-1.0), -1e50]), 1e-100)
        self.assertRaises(OverflowError, math.fsum, [1e+308, 1e+308])
        self.assertRaises(ValueError, math.fsum, [math.inf, -math.inf])
        self.assertRaises(TypeError, math.fsum, ['spam'])
        self.assertRaises(TypeError, math.fsum, 1)
        self.assertRaises(OverflowError, math.fsum, [10**1000])

        def bad_iter():
            yield 1.0
            raise ZeroDivisionError

        self.assertRaises(ZeroDivisionError, math.fsum, bad_iter())