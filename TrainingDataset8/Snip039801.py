def test_for_statement(self):
        """Test for statements"""
        CODE_FOR_STATEMENT = """
a = 1
for i in range(10):
    for j in range(2):
        a

"""
        self._testCode(CODE_FOR_STATEMENT, 1)