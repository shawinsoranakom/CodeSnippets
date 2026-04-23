def test_dictsort_complex_sorting_key(self):
        """
        Since dictsort uses dict.get()/getattr() under the hood, it can sort
        on keys like 'foo.bar'.
        """
        data = [
            {"foo": {"bar": 1, "baz": "c"}},
            {"foo": {"bar": 2, "baz": "b"}},
            {"foo": {"bar": 3, "baz": "a"}},
        ]
        sorted_data = dictsort(data, "foo.baz")

        self.assertEqual([d["foo"]["bar"] for d in sorted_data], [3, 2, 1])