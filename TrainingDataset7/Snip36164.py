def test_reversed(self):
        s = reversed(OrderedSet([1, 2, 3]))
        self.assertIsInstance(s, collections.abc.Iterator)
        self.assertEqual(list(s), [3, 2, 1])