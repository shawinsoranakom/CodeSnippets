def test_value(self):
        """Test the hash of functions with values."""

        def f():
            x = 42
            return x

        def g():
            x = 12
            return x

        def h():
            y = 42
            return y

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))