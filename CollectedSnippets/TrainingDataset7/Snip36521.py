def test_contains(self):
        test_data = [
            ("c", "abcde"),
            (2, [1, 2, 3]),
            ("a", {"a": 1, "b": 2, "c": 3}),
            (2, {1, 2, 3}),
        ]
        for needle, haystack in test_data:
            self.assertIn(needle, self.lazy_wrap(haystack))

        # __contains__ doesn't work when the haystack is a string and the
        # needle a LazyObject.
        for needle_haystack in test_data[1:]:
            self.assertIn(self.lazy_wrap(needle), haystack)
            self.assertIn(self.lazy_wrap(needle), self.lazy_wrap(haystack))