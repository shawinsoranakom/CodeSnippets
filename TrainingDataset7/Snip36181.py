def test_setdefault(self):
        x = MultiValueDict({"a": [1, 2]})
        a = x.setdefault("a", 3)
        b = x.setdefault("b", 3)
        self.assertEqual(a, 2)
        self.assertEqual(b, 3)
        self.assertEqual(list(x.lists()), [("a", [1, 2]), ("b", [3])])