def test_some_keyword_only_params(self):
        """Works when keeping some params as positional-or-keyword."""

        @deprecate_posargs(RemovedAfterNextVersionWarning, ["b"])
        def some_func(a, *, b=1):
            return a, b

        with self.assertDeprecated("'b'", "some_func"):
            result = some_func(10, 20)
        self.assertEqual(result, (10, 20))