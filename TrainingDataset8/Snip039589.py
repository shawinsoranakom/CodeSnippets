def test_simple(self):
        """Test the hash of simple functions."""

        def f(x):
            return x * x

        def g(x):
            return x + x

        def h(x):
            return x * x

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))