def test_tuples(self):
        self.assertEqual(urlencode((("a", 1), ("b", 2), ("c", 3))), "a=1&b=2&c=3")