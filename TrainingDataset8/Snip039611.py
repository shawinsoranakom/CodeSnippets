def test_ufunc(self):
        """Test code that references numpy ufuncs."""

        def f(a, b):
            return np.logical_and(a, b)

        def g(a, b):
            return np.logical_and(a, b)

        def h(a, b):
            return np.remainder(a, b)

        self.assertNotEqual(get_hash(np.remainder), get_hash(np.logical_and))
        self.assertEqual(get_hash(f), get_hash(g))
        self.assertNotEqual(get_hash(f), get_hash(h))