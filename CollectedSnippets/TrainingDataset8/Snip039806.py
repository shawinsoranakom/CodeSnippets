def test_yield_statement(self):
        """Test that 'yield' expressions do not get magicked"""
        CODE_YIELD_STATEMENT = """
def yield_func():
    yield
"""
        self._testCode(CODE_YIELD_STATEMENT, 0)