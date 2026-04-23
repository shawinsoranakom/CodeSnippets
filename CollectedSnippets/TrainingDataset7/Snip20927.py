async def test_markcoroutinefunction_applied(self):
        class Test:
            @async_simple_dec_m
            async def method(self):
                return "tests"

        method = Test().method
        self.assertIs(iscoroutinefunction(method), True)
        self.assertEqual(await method(), "returned: tests")