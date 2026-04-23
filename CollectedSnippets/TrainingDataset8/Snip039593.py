def test_referenced(self):
        """Test the hash of functions that reference values."""

        x = 42
        y = 123

        def f():
            return x

        def g():
            return y

        def h():
            return x

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))