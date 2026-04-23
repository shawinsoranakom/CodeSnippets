def testDist(self):
        from decimal import Decimal as D
        from fractions import Fraction as F

        dist = math.dist
        sqrt = math.sqrt

        # Simple exact cases
        self.assertEqual(dist((1.0, 2.0, 3.0), (4.0, 2.0, -1.0)), 5.0)
        self.assertEqual(dist((1, 2, 3), (4, 2, -1)), 5.0)

        # Test different numbers of arguments (from zero to nine)
        # against a straightforward pure python implementation
        for i in range(9):
            for j in range(5):
                p = tuple(random.uniform(-5, 5) for k in range(i))
                q = tuple(random.uniform(-5, 5) for k in range(i))
                self.assertAlmostEqual(
                    dist(p, q),
                    sqrt(sum((px - qx) ** 2.0 for px, qx in zip(p, q)))
                )

        # Test non-tuple inputs
        self.assertEqual(dist([1.0, 2.0, 3.0], [4.0, 2.0, -1.0]), 5.0)
        self.assertEqual(dist(iter([1.0, 2.0, 3.0]), iter([4.0, 2.0, -1.0])), 5.0)

        # Test allowable types (those with __float__)
        self.assertEqual(dist((14.0, 1.0), (2.0, -4.0)), 13.0)
        self.assertEqual(dist((14, 1), (2, -4)), 13)
        self.assertEqual(dist((FloatLike(14.), 1), (2, -4)), 13)
        self.assertEqual(dist((11, 1), (FloatLike(-1.), -4)), 13)
        self.assertEqual(dist((14, FloatLike(-1.)), (2, -6)), 13)
        self.assertEqual(dist((14, -1), (2, -6)), 13)
        self.assertEqual(dist((D(14), D(1)), (D(2), D(-4))), D(13))
        self.assertEqual(dist((F(14, 32), F(1, 32)), (F(2, 32), F(-4, 32))),
                         F(13, 32))
        self.assertEqual(dist((True, True, False, False, True, True),
                              (True, False, True, False, False, False)),
                         2.0)

        # Test corner cases
        self.assertEqual(dist((13.25, 12.5, -3.25),
                              (13.25, 12.5, -3.25)),
                         0.0)                      # Distance with self is zero
        self.assertEqual(dist((), ()), 0.0)        # Zero-dimensional case
        self.assertEqual(1.0,                      # Convert negative zero to positive zero
            math.copysign(1.0, dist((-0.0,), (0.0,)))
        )
        self.assertEqual(1.0,                      # Convert negative zero to positive zero
            math.copysign(1.0, dist((0.0,), (-0.0,)))
        )
        self.assertEqual(                          # Handling of moving max to the end
            dist((1.5, 1.5, 0.5), (0, 0, 0)),
            dist((1.5, 0.5, 1.5), (0, 0, 0))
        )

        # Verify tuple subclasses are allowed
        with torch._dynamo.error_on_graph_break(False):
            class T(tuple):
                pass
        self.assertEqual(dist(T((1, 2, 3)), ((4, 2, -1))), 5.0)

        # Test handling of bad arguments
        with self.assertRaises(TypeError):         # Reject keyword args
            dist(p=(1, 2, 3), q=(4, 5, 6))
        with self.assertRaises(TypeError):         # Too few args
            dist((1, 2, 3))
        with self.assertRaises(TypeError):         # Too many args
            dist((1, 2, 3), (4, 5, 6), (7, 8, 9))
        with self.assertRaises(TypeError):         # Scalars not allowed
            dist(1, 2)
        with self.assertRaises(TypeError):         # Reject values without __float__
            dist((1.1, 'string', 2.2), (1, 2, 3))
        with self.assertRaises(ValueError):        # Check dimension agree
            dist((1, 2, 3, 4), (5, 6, 7))
        with self.assertRaises(ValueError):        # Check dimension agree
            dist((1, 2, 3), (4, 5, 6, 7))
        with self.assertRaises(TypeError):
            dist((1,)*17 + ("spam",), (1,)*18)
        with self.assertRaises(TypeError):         # Rejects invalid types
            dist("abc", "xyz")
        int_too_big_for_float = 10 ** (sys.float_info.max_10_exp + 5)
        with self.assertRaises((ValueError, OverflowError)):
            dist((1, int_too_big_for_float), (2, 3))
        with self.assertRaises((ValueError, OverflowError)):
            dist((2, 3), (1, int_too_big_for_float))
        with self.assertRaises(TypeError):
            dist((1,), 2)
        with self.assertRaises(TypeError):
            dist([1], 2)

        with torch._dynamo.error_on_graph_break(False):
            class BadFloat:
                __float__ = BadDescr()

        with self.assertRaises(ValueError):
            dist([1], [BadFloat()])

        # Verify that the one dimensional case is equivalent to abs()
        for i in range(20):
            p, q = random.random(), random.random()
            self.assertEqual(dist((p,), (q,)), abs(p - q))

        # Test special values
        values = [NINF, -10.5, -0.0, 0.0, 10.5, INF, NAN]
        for p in itertools.product(values, repeat=3):
            for q in itertools.product(values, repeat=3):
                diffs = [px - qx for px, qx in zip(p, q)]
                if any(map(math.isinf, diffs)):
                    # Any infinite difference gives positive infinity.
                    self.assertEqual(dist(p, q), INF)
                elif any(map(math.isnan, diffs)):
                    # If no infinity, any NaN gives a NaN.
                    self.assertTrue(math.isnan(dist(p, q)))

        # Verify scaling for extremely large values
        fourthmax = FLOAT_MAX / 4.0
        for n in range(32):
            p = (fourthmax,) * n
            q = (0.0,) * n
            self.assertTrue(math.isclose(dist(p, q), fourthmax * math.sqrt(n)))
            self.assertTrue(math.isclose(dist(q, p), fourthmax * math.sqrt(n)))

        # Verify scaling for extremely small values
        for exp in range(32):
            scale = FLOAT_MIN / 2.0 ** exp
            p = (4*scale, 3*scale)
            q = (0.0, 0.0)
            self.assertEqual(math.dist(p, q), 5*scale)
            self.assertEqual(math.dist(q, p), 5*scale)