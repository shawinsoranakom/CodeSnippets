def test_sqrtprod_helper_function_fundamentals(self):
        # Verify that results are close to sqrt(x * y)
        for i in range(100):
            x = random.expovariate()
            y = random.expovariate()
            expected = math.sqrt(x * y)
            actual = statistics._sqrtprod(x, y)
            with self.subTest(x=x, y=y, expected=expected, actual=actual):
                self.assertAlmostEqual(expected, actual)

        x, y, target = 0.8035720646477457, 0.7957468097636939, 0.7996498651651661
        self.assertEqual(statistics._sqrtprod(x, y), target)
        self.assertNotEqual(math.sqrt(x * y), target)

        # Test that range extremes avoid underflow and overflow
        smallest = sys.float_info.min * sys.float_info.epsilon
        self.assertEqual(statistics._sqrtprod(smallest, smallest), smallest)
        biggest = sys.float_info.max
        self.assertEqual(statistics._sqrtprod(biggest, biggest), biggest)

        # Check special values and the sign of the result
        special_values = [0.0, -0.0, 1.0, -1.0, 4.0, -4.0,
                          math.nan, -math.nan, math.inf, -math.inf]
        for x, y in itertools.product(special_values, repeat=2):
            try:
                expected = math.sqrt(x * y)
            except ValueError:
                expected = 'ValueError'
            try:
                actual = statistics._sqrtprod(x, y)
            except ValueError:
                actual = 'ValueError'
            with self.subTest(x=x, y=y, expected=expected, actual=actual):
                if isinstance(expected, str) and expected == 'ValueError':
                    self.assertEqual(actual, 'ValueError')
                    continue
                self.assertIsInstance(actual, float)
                if math.isnan(expected):
                    self.assertTrue(math.isnan(actual))
                    continue
                self.assertEqual(actual, expected)
                self.assertEqual(sign(actual), sign(expected))