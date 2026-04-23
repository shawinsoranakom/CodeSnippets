def test_rename(self):
        """Test the hash of function with renamed variables."""

        def f(x, y):
            return x + y

        def g(x, y):
            return y + x

        def h(y, x):
            return y + x

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))