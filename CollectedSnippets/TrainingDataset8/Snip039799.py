def test_simple_statement(self):
        """Test simple statements"""
        CODE_SIMPLE_STATEMENTS = """
a = 1
b = 10
a
b
"""
        self._testCode(CODE_SIMPLE_STATEMENTS, 2)