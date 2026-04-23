def testComb(self):
        comb = math.comb
        factorial = math.factorial
        # Test if factorial definition is satisfied
        for n in range(500):
            for k in (range(n + 1) if n < 100 else range(30) if n < 200 else range(10)):
                self.assertEqual(comb(n, k), factorial(n)
                    // (factorial(k) * factorial(n - k)))

        # Test for Pascal's identity
        for n in range(1, 100):
            for k in range(1, n):
                self.assertEqual(comb(n, k), comb(n - 1, k - 1) + comb(n - 1, k))

        # Test corner cases
        for n in range(100):
            self.assertEqual(comb(n, 0), 1)
            self.assertEqual(comb(n, n), 1)

        for n in range(1, 100):
            self.assertEqual(comb(n, 1), n)
            self.assertEqual(comb(n, n - 1), n)

        # Test Symmetry
        for n in range(100):
            for k in range(n // 2):
                self.assertEqual(comb(n, k), comb(n, n - k))

        # Raises TypeError if any argument is non-integer or argument count is
        # not 2
        self.assertRaises(TypeError, comb, 10, 1.0)
        self.assertRaises(TypeError, comb, 10, decimal.Decimal(1.0))
        self.assertRaises(TypeError, comb, 10, "1")
        self.assertRaises(TypeError, comb, 10.0, 1)
        self.assertRaises(TypeError, comb, decimal.Decimal(10.0), 1)
        self.assertRaises(TypeError, comb, "10", 1)

        self.assertRaises(TypeError, comb, 10)
        self.assertRaises(TypeError, comb, 10, 1, 3)
        self.assertRaises(TypeError, comb)

        # Raises Value error if not k or n are negative numbers
        self.assertRaises(ValueError, comb, -1, 1)
        self.assertRaises(ValueError, comb, -2**1000, 1)
        self.assertRaises(ValueError, comb, 1, -1)
        self.assertRaises(ValueError, comb, 1, -2**1000)

        # Returns zero if k is greater than n
        self.assertEqual(comb(1, 2), 0)
        self.assertEqual(comb(1, 2**1000), 0)

        n = 2**1000
        self.assertEqual(comb(n, 0), 1)
        self.assertEqual(comb(n, 1), n)
        self.assertEqual(comb(n, 2), n * (n-1) // 2)
        self.assertEqual(comb(n, n), 1)
        self.assertEqual(comb(n, n-1), n)
        self.assertEqual(comb(n, n-2), n * (n-1) // 2)
        if support.check_impl_detail(cpython=True):
            self.assertRaises(OverflowError, comb, n, n//2)

        for n, k in (True, True), (True, False), (False, False):
            self.assertEqual(comb(n, k), 1)
            self.assertIs(type(comb(n, k)), int)
        self.assertEqual(comb(IntSubclass(5), IntSubclass(2)), 10)
        self.assertEqual(comb(MyIndexable(5), MyIndexable(2)), 10)
        for k in range(3):
            self.assertIs(type(comb(IntSubclass(5), IntSubclass(k))), int)
            self.assertIs(type(comb(MyIndexable(5), MyIndexable(k))), int)