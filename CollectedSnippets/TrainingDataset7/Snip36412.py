def test_dict(self):
        result = urlencode({"a": 1, "b": 2, "c": 3})
        self.assertEqual(result, "a=1&b=2&c=3")