def testPerm(self):
        perm = math.perm
        factorial = math.factorial
        # Test if factorial definition is satisfied
        for n in range(500):
            for k in (range(n + 1) if n < 100 else range(30) if n < 200 else range(10)):
                self.assertEqual(perm(n, k),
                                 factorial(n) // factorial(n - k))

        # Test for Pascal's identity
        for n in range(1, 100):
            for k in range(1, n):
                self.assertEqual(perm(n, k), perm(n - 1, k - 1) * k + perm(n - 1, k))

        # Test corner cases
        for n in range(1, 100):
            self.assertEqual(perm(n, 0), 1)
            self.assertEqual(perm(n, 1), n)
            self.assertEqual(perm(n, n), factorial(n))

        # Test one argument form
        for n in range(20):
            self.assertEqual(perm(n), factorial(n))
            self.assertEqual(perm(n, None), factorial(n))

        # Raises TypeError if any argument is non-integer or argument count is
        # not 1 or 2
        self.assertRaises(TypeError, perm, 10, 1.0)
        self.assertRaises(TypeError, perm, 10, decimal.Decimal(1.0))
        self.assertRaises(TypeError, perm, 10, "1")
        self.assertRaises(TypeError, perm, 10.0, 1)
        self.assertRaises(TypeError, perm, decimal.Decimal(10.0), 1)
        self.assertRaises(TypeError, perm, "10", 1)

        self.assertRaises(TypeError, perm)
        self.assertRaises(TypeError, perm, 10, 1, 3)
        self.assertRaises(TypeError, perm)

        # Raises Value error if not k or n are negative numbers
        self.assertRaises(ValueError, perm, -1, 1)
        self.assertRaises(ValueError, perm, -2**1000, 1)
        self.assertRaises(ValueError, perm, 1, -1)
        self.assertRaises(ValueError, perm, 1, -2**1000)

        # Returns zero if k is greater than n
        self.assertEqual(perm(1, 2), 0)
        self.assertEqual(perm(1, 2**1000), 0)

        n = 2**1000
        self.assertEqual(perm(n, 0), 1)
        self.assertEqual(perm(n, 1), n)
        self.assertEqual(perm(n, 2), n * (n-1))
        if support.check_impl_detail(cpython=True):
            self.assertRaises(OverflowError, perm, n, n)

        for n, k in (True, True), (True, False), (False, False):
            self.assertEqual(perm(n, k), 1)
            self.assertIs(type(perm(n, k)), int)
        self.assertEqual(perm(IntSubclass(5), IntSubclass(2)), 20)
        self.assertEqual(perm(MyIndexable(5), MyIndexable(2)), 20)
        for k in range(3):
            self.assertIs(type(perm(IntSubclass(5), IntSubclass(k))), int)
            self.assertIs(type(perm(MyIndexable(5), MyIndexable(k))), int)