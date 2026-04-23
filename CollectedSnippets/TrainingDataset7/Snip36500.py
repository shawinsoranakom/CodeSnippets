def test_converts_json_types(self):
        for test_case, expected in [
            (None, "null"),
            (True, "true"),
            (False, "false"),
            (2, "2"),
            (3.0, "3.0"),
            (1e23 + 1, "1e+23"),
            ("1", '"1"'),
            (b"hello", '"hello"'),
            ([], "[]"),
            (UserList([1, 2]), "[1, 2]"),
            ({}, "{}"),
            ({1: "a"}, '{"1": "a"}'),
            ({"foo": (1, 2, 3)}, '{"foo": [1, 2, 3]}'),
            (defaultdict(list), "{}"),
            (float("nan"), "NaN"),
            (float("inf"), "Infinity"),
            (float("-inf"), "-Infinity"),
        ]:
            with self.subTest(test_case):
                normalized = normalize_json(test_case)
                # Ensure that the normalized result is serializable.
                self.assertEqual(json.dumps(normalized), expected)