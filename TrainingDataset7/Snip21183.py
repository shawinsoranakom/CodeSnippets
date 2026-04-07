def test_no_warning_when_not_needed(self):
        @deprecate_posargs(RemovedAfterNextVersionWarning, ["b"])
        def some_func(a=0, *, b=1):
            return a, b

        with self.subTest("All arguments supplied"), self.assertNoLogs(level="WARNING"):
            result = some_func(10, b=20)
            self.assertEqual(result, (10, 20))

        with self.subTest("All default arguments"), self.assertNoLogs(level="WARNING"):
            result = some_func()
            self.assertEqual(result, (0, 1))

        with (
            self.subTest("Partial arguments supplied"),
            self.assertNoLogs(level="WARNING"),
        ):
            result = some_func(10)
            self.assertEqual(result, (10, 1))