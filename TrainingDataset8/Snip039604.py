def test_coref(self):
        """Test code that references itself."""

        def f(x):
            return f(x)

        def g(x):
            return g(x) + 1

        def h(x):
            return h(x)

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))