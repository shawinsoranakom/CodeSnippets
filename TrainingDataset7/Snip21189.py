def test_positional_only_params(self):
        @deprecate_posargs(RemovedAfterNextVersionWarning, ["c"])
        def some_func(a, /, b, *, c=3):
            return a, b, c

        with self.assertDeprecated("'c'", "some_func"):
            result = some_func(10, 20, 30)
        self.assertEqual(result, (10, 20, 30))