def test_group_named(self):
        pattern = r"(?P<first_group_name>.*)-(?P<second_group_name>.*)"
        expected = [
            (
                "%(first_group_name)s-%(second_group_name)s",
                ["first_group_name", "second_group_name"],
            )
        ]
        result = regex_helper.normalize(pattern)
        self.assertEqual(result, expected)