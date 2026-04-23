def test_if_statement(self):
        """Test if statements"""
        CODE_IF_STATEMENT = """
a = 1
if True:
    a
    if False:
        a
    elif False:
        a
    else:
        a
else:
    a
"""
        self._testCode(CODE_IF_STATEMENT, 5)