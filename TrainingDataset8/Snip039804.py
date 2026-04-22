def test_with_statement(self):
        """Test 'with' statements"""
        CODE_WITH_STATEMENT = """
a = 10
with None:
    a
"""
        self._testCode(CODE_WITH_STATEMENT, 1)