def test_getlist_none_empty_values(self):
        x = MultiValueDict({"a": None, "b": []})
        self.assertIsNone(x.getlist("a"))
        self.assertEqual(x.getlist("b"), [])