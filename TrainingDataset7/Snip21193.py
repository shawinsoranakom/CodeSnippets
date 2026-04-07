async def test_async(self):
        """A decorated async function is still async."""

        @deprecate_posargs(RemovedAfterNextVersionWarning, ["a", "b"])
        async def some_func(*, a, b=1):
            return a, b

        self.assertTrue(inspect.iscoroutinefunction(some_func.__wrapped__))
        self.assertTrue(inspect.iscoroutinefunction(some_func))

        with (
            self.subTest("With deprecation warning"),
            self.assertDeprecated("'a', 'b'", "some_func"),
        ):
            result = await some_func(10, 20)
            self.assertEqual(result, (10, 20))

        with (
            self.subTest("Without deprecation warning"),
            self.assertNoLogs(level="WARNING"),
        ):
            result = await some_func(a=10, b=20)
            self.assertEqual(result, (10, 20))