def test_update_with_iterable_of_pairs(self):
        for value in [(("a", 1),), [("a", 1)], {("a", 1)}]:
            d = MultiValueDict()
            d.update(value)
            self.assertEqual(d, MultiValueDict({"a": [1]}))