def test_internal_getlist_does_mutate(self):
        x = MultiValueDict({"a": ["1", "2"], "b": ["3"]})
        values = x._getlist("a")
        values += x._getlist("b")
        self.assertEqual(x._getlist("a"), ["1", "2", "3"])