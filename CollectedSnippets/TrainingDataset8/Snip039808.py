def test_await_expression(self):
        """Test that 'await' expressions do not get magicked"""
        CODE_AWAIT_EXPRESSION = """
async def await_func(a):
    await coro()
"""
        self._testCode(CODE_AWAIT_EXPRESSION, 0)