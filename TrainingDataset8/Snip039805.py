def test_while_statement(self):
        """Test 'while' statements"""
        CODE_WHILE_STATEMENT = """
a = 10
while True:
    a
"""
        self._testCode(CODE_WHILE_STATEMENT, 1)