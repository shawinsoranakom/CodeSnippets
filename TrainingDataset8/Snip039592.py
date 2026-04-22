def test_defaults(self):
        """Test the hash of functions with defaults."""

        def f(x=42):
            return x

        def g(x=12):
            return x

        def h(x=42):
            return x

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))