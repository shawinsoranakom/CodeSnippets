def test_sort(self):
        sorted_dicts = dictsort(
            [
                {"age": 23, "name": "Barbara-Ann"},
                {"age": 63, "name": "Ra Ra Rasputin"},
                {"name": "Jonny B Goode", "age": 18},
            ],
            "age",
        )

        self.assertEqual(
            [sorted(dict.items()) for dict in sorted_dicts],
            [
                [("age", 18), ("name", "Jonny B Goode")],
                [("age", 23), ("name", "Barbara-Ann")],
                [("age", 63), ("name", "Ra Ra Rasputin")],
            ],
        )