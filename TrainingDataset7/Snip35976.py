def test_is_ignored_path_true(self):
        patterns = (
            ["foo/bar/baz"],
            ["baz"],
            ["foo/bar/baz"],
            ["*/baz"],
            ["*"],
            ["b?z"],
            ["[abc]az"],
            ["*/ba[!z]/baz"],
        )
        for ignore_patterns in patterns:
            with self.subTest(ignore_patterns=ignore_patterns):
                self.assertIs(
                    is_ignored_path("foo/bar/baz", ignore_patterns=ignore_patterns),
                    True,
                )