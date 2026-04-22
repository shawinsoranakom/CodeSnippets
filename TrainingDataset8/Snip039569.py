def test_partial(self):
        p1 = functools.partial(int, base=2)
        p2 = functools.partial(int, base=3)
        p3 = functools.partial(int, base=2)

        self.assertEqual(get_hash(p1), get_hash(p3))
        self.assertNotEqual(get_hash(p1), get_hash(p2))