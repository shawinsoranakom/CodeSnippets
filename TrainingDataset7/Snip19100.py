def test_data_types(self):
        # Many different data types can be cached
        tests = {
            "string": "this is a string",
            "int": 42,
            "bool": True,
            "list": [1, 2, 3, 4],
            "tuple": (1, 2, 3, 4),
            "dict": {"A": 1, "B": 2},
            "function": f,
            "class": C,
        }
        for key, value in tests.items():
            with self.subTest(key=key):
                cache.set(key, value)
                self.assertEqual(cache.get(key), value)