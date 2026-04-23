def test_fma_infinities(self):
        # Cases involving infinite inputs or results.
        positives = [1e-300, 2.3, 1e300, math.inf]
        finites = [-1e300, -2.3, -1e-300, -0.0, 0.0, 1e-300, 2.3, 1e300]
        non_nans = [-math.inf, -2.3, -0.0, 0.0, 2.3, math.inf]

        # ValueError due to inf * 0 computation.
        for c in non_nans:
            for infinity in [math.inf, -math.inf]:
                for zero in [0.0, -0.0]:
                    with self.subTest(c=c, infinity=infinity, zero=zero):
                        with self.assertRaises(ValueError):
                            math.fma(infinity, zero, c)
                        with self.assertRaises(ValueError):
                            math.fma(zero, infinity, c)

        # ValueError when a*b and c both infinite of opposite signs.
        for b in positives:
            with self.subTest(b=b):
                with self.assertRaises(ValueError):
                    math.fma(math.inf, b, -math.inf)
                with self.assertRaises(ValueError):
                    math.fma(math.inf, -b, math.inf)
                with self.assertRaises(ValueError):
                    math.fma(-math.inf, -b, -math.inf)
                with self.assertRaises(ValueError):
                    math.fma(-math.inf, b, math.inf)
                with self.assertRaises(ValueError):
                    math.fma(b, math.inf, -math.inf)
                with self.assertRaises(ValueError):
                    math.fma(-b, math.inf, math.inf)
                with self.assertRaises(ValueError):
                    math.fma(-b, -math.inf, -math.inf)
                with self.assertRaises(ValueError):
                    math.fma(b, -math.inf, math.inf)

        # Infinite result when a*b and c both infinite of the same sign.
        for b in positives:
            with self.subTest(b=b):
                self.assertEqual(math.fma(math.inf, b, math.inf), math.inf)
                self.assertEqual(math.fma(math.inf, -b, -math.inf), -math.inf)
                self.assertEqual(math.fma(-math.inf, -b, math.inf), math.inf)
                self.assertEqual(math.fma(-math.inf, b, -math.inf), -math.inf)
                self.assertEqual(math.fma(b, math.inf, math.inf), math.inf)
                self.assertEqual(math.fma(-b, math.inf, -math.inf), -math.inf)
                self.assertEqual(math.fma(-b, -math.inf, math.inf), math.inf)
                self.assertEqual(math.fma(b, -math.inf, -math.inf), -math.inf)

        # Infinite result when a*b finite, c infinite.
        for a, b in itertools.product(finites, finites):
            with self.subTest(b=b):
                self.assertEqual(math.fma(a, b, math.inf), math.inf)
                self.assertEqual(math.fma(a, b, -math.inf), -math.inf)

        # Infinite result when a*b infinite, c finite.
        for b, c in itertools.product(positives, finites):
            with self.subTest(b=b, c=c):
                self.assertEqual(math.fma(math.inf, b, c), math.inf)
                self.assertEqual(math.fma(-math.inf, b, c), -math.inf)
                self.assertEqual(math.fma(-math.inf, -b, c), math.inf)
                self.assertEqual(math.fma(math.inf, -b, c), -math.inf)

                self.assertEqual(math.fma(b, math.inf, c), math.inf)
                self.assertEqual(math.fma(b, -math.inf, c), -math.inf)
                self.assertEqual(math.fma(-b, -math.inf, c), math.inf)
                self.assertEqual(math.fma(-b, math.inf, c), -math.inf)