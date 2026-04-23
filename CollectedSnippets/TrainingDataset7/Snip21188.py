def test_variable_kwargs(self):
        """Works with **kwargs."""

        @deprecate_posargs(RemovedAfterNextVersionWarning, ["b"])
        def some_func(a, *, b=1, **kwargs):
            return a, b, kwargs

        with (
            self.subTest("Called with additional kwargs"),
            self.assertDeprecated("'b'", "some_func"),
        ):
            result = some_func(10, 20, c=30)
            self.assertEqual(result, (10, 20, {"c": 30}))

        with (
            self.subTest("Called without additional kwargs"),
            self.assertDeprecated("'b'", "some_func"),
        ):
            result = some_func(10, 20)
            self.assertEqual(result, (10, 20, {}))

        with (
            self.subTest("Called with too many positional arguments"),
            # Similar to test_detects_extra_positional_arguments() above,
            # but verifying logic is not confused by variable **kwargs.
            self.assertRaisesMessage(
                TypeError,
                "some_func() takes at most 2 positional argument(s) (including 1 "
                "deprecated) but 3 were given.",
            ),
        ):
            some_func(10, 20, 30)

        with self.subTest("No warning needed"):
            result = some_func(10, b=20, c=30)
            self.assertEqual(result, (10, 20, {"c": 30}))