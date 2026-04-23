def test_group_positional(self):
        pattern = r"(.*)-(.+)"
        expected = [("%(_0)s-%(_1)s", ["_0", "_1"])]
        result = regex_helper.normalize(pattern)
        self.assertEqual(result, expected)