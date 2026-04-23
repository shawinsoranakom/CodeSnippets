def test_detects_duplicate_arguments(self):
        @deprecate_posargs(RemovedAfterNextVersionWarning, ["b", "c"])
        def func(a, *, b=1, c=2):
            return a, b, c

        msg = (
            "func() got both deprecated positional and keyword argument values for {0}"
        )
        with (
            self.subTest("One duplicate"),
            self.assertRaisesMessage(TypeError, msg.format("'b'")),
        ):
            func(0, 10, b=12)

        with (
            self.subTest("Multiple duplicates"),
            self.assertRaisesMessage(TypeError, msg.format("'b', 'c'")),
        ):
            func(0, 10, 20, b=12, c=22)

        with (
            self.subTest("No false positives for valid kwargs"),
            # Deprecation warning for 'b', not TypeError for duplicate 'c'.
            self.assertDeprecated("'b'", "func"),
        ):
            result = func(0, 11, c=22)
            self.assertEqual(result, (0, 11, 22))