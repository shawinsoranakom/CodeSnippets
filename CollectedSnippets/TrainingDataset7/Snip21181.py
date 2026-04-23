def test_all_keyword_only_params(self):
        """All positional arguments are remapped to keyword-only arguments."""

        @deprecate_posargs(RemovedAfterNextVersionWarning, ["a", "b"])
        def some_func(*, a=1, b=2):
            return a, b

        with (
            self.subTest("Multiple affected args"),
            self.assertDeprecated("'a', 'b'", "some_func"),
        ):
            result = some_func(10, 20)
            self.assertEqual(result, (10, 20))

        with (
            self.subTest("One affected arg"),
            self.assertDeprecated("'a'", "some_func"),
        ):
            result = some_func(10)
            self.assertEqual(result, (10, 2))