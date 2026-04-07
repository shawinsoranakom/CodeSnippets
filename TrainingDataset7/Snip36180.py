def test_setitem(self):
        x = MultiValueDict({"a": [1, 2]})
        x["a"] = 3
        self.assertEqual(list(x.lists()), [("a", [3])])