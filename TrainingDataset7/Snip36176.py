def test_getlist_doesnt_mutate(self):
        x = MultiValueDict({"a": ["1", "2"], "b": ["3"]})
        values = x.getlist("a")
        values += x.getlist("b")
        self.assertEqual(x.getlist("a"), ["1", "2"])