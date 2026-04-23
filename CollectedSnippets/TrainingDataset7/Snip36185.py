def test_update_multivaluedict_arg(self):
        x = MultiValueDict({"a": [1], "b": [2], "c": [3]})
        x.update(MultiValueDict({"a": [4], "b": [5]}))
        self.assertEqual(list(x.lists()), [("a", [1, 4]), ("b", [2, 5]), ("c", [3])])