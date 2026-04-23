def test_yield_from_statement(self):
        """Test that 'yield from' expressions do not get magicked"""
        CODE_YIELD_FROM_STATEMENT = """
def yield_func():
    yield from None
"""
        self._testCode(CODE_YIELD_FROM_STATEMENT, 0)