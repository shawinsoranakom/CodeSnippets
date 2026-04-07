def test_sort_list_of_tuples(self):
        data = [("a", "42"), ("c", "string"), ("b", "foo")]
        expected = [("a", "42"), ("b", "foo"), ("c", "string")]
        self.assertEqual(dictsort(data, 0), expected)