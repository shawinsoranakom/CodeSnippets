def test_repr(self):
        self.assertEqual(repr(OrderedSet()), "OrderedSet()")
        self.assertEqual(repr(OrderedSet([2, 3, 2, 1])), "OrderedSet([2, 3, 1])")