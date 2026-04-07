def test_sort_list_of_tuples(self):
        data = [("a", "42"), ("c", "string"), ("b", "foo")]
        expected = [("c", "string"), ("b", "foo"), ("a", "42")]
        self.assertEqual(dictsortreversed(data, 0), expected)