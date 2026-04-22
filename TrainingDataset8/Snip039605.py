def test_multiple(self):
        """Test code that references multiple objects."""

        x = 12
        y = 13
        z = 14

        def f():
            return x + z

        def g():
            return y + z

        def h():
            return x + z

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))