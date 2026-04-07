def test_sort_list_of_tuple_like_dicts(self):
        data = [
            {"0": "a", "1": "42"},
            {"0": "c", "1": "string"},
            {"0": "b", "1": "foo"},
        ]
        expected = [
            {"0": "c", "1": "string"},
            {"0": "b", "1": "foo"},
            {"0": "a", "1": "42"},
        ]
        self.assertEqual(dictsortreversed(data, "0"), expected)