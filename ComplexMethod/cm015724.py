def test_pow(self):
        self.assertAlmostEqual(pow(1+1j, 0+0j), 1.0)
        self.assertAlmostEqual(pow(0+0j, 2+0j), 0.0)
        self.assertEqual(pow(0+0j, 2000+0j), 0.0)
        self.assertEqual(pow(0, 0+0j), 1.0)
        self.assertEqual(pow(-1, 0+0j), 1.0)
        self.assertRaises(ZeroDivisionError, pow, 0+0j, 1j)
        self.assertRaises(ZeroDivisionError, pow, 0+0j, -1000)
        self.assertAlmostEqual(pow(1j, -1), 1/1j)
        self.assertAlmostEqual(pow(1j, 200), 1)
        self.assertRaises(ValueError, pow, 1+1j, 1+1j, 1+1j)
        self.assertRaises(OverflowError, pow, 1e200+1j, 1e200+1j)
        self.assertRaises(TypeError, pow, 1j, None)
        self.assertRaises(TypeError, pow, None, 1j)
        self.assertAlmostEqual(pow(1j, 0.5), 0.7071067811865476+0.7071067811865475j)

        a = 3.33+4.43j
        self.assertEqual(a ** 0j, 1)
        self.assertEqual(a ** 0.+0.j, 1)

        self.assertEqual(3j ** 0j, 1)
        self.assertEqual(3j ** 0, 1)

        try:
            0j ** a
        except ZeroDivisionError:
            pass
        else:
            self.fail("should fail 0.0 to negative or complex power")

        try:
            0j ** (3-2j)
        except ZeroDivisionError:
            pass
        else:
            self.fail("should fail 0.0 to negative or complex power")

        # The following is used to exercise certain code paths
        self.assertEqual(a ** 105, a ** 105)
        self.assertEqual(a ** -105, a ** -105)
        self.assertEqual(a ** -30, a ** -30)

        self.assertEqual(0.0j ** 0, 1)

        b = 5.1+2.3j
        self.assertRaises(ValueError, pow, a, b, 0)

        # Check some boundary conditions; some of these used to invoke
        # undefined behaviour (https://bugs.python.org/issue44698). We're
        # not actually checking the results of these operations, just making
        # sure they don't crash (for example when using clang's
        # UndefinedBehaviourSanitizer).
        values = (sys.maxsize, sys.maxsize+1, sys.maxsize-1,
                  -sys.maxsize, -sys.maxsize+1, -sys.maxsize+1)
        for real in values:
            for imag in values:
                with self.subTest(real=real, imag=imag):
                    c = complex(real, imag)
                    try:
                        c ** real
                    except OverflowError:
                        pass
                    try:
                        c ** c
                    except OverflowError:
                        pass

        # gh-113841: possible undefined division by 0 in _Py_c_pow()
        x, y = 9j, 33j**3
        with self.assertRaises(OverflowError):
            x**y