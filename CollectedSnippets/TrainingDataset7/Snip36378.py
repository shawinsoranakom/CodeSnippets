def test_count_equal(self):
        tests = (
            ({"a": 1, "b": ["a", 1]}, (("a", 1), ("b", ("a", 1)))),
            ({"a": 1, "b": ("a", [1, 2])}, (("a", 1), ("b", ("a", (1, 2))))),
        )
        for value, expected in tests:
            with self.subTest(value=value):
                self.assertCountEqual(make_hashable(value), expected)