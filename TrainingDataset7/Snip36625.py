def test_group_noncapturing(self):
        pattern = r"(?:non-capturing)"
        expected = [("non-capturing", [])]
        result = regex_helper.normalize(pattern)
        self.assertEqual(result, expected)