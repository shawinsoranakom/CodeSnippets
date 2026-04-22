def test_async_function_statement(self):
        """Test async function definitions"""
        CODE_ASYNC_FUNCTION = """
async def myfunc(a):
    a
"""
        self._testCode(CODE_ASYNC_FUNCTION, 1)