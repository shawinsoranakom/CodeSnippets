def test_async_with_statement(self):
        """Test 'async with' statements"""
        CODE_ASYNC_WITH = """
async def myfunc(a):
    async with None:
        a
"""
        self._testCode(CODE_ASYNC_WITH, 1)