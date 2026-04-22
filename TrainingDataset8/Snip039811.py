def test_async_for_statement(self):
        """Test 'async for' statements"""
        CODE_ASYNC_FOR = """
async def myfunc(a):
    async for _ in None:
        a
"""
        self._testCode(CODE_ASYNC_FOR, 1)