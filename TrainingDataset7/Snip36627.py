def test_group_backreference(self):
        pattern = r"(?P<first_group_name>.*)-(?P=first_group_name)"
        expected = [("%(first_group_name)s-%(first_group_name)s", ["first_group_name"])]
        result = regex_helper.normalize(pattern)
        self.assertEqual(result, expected)