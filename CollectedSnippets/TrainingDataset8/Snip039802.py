def test_try_statement(self):
        """Test try statements"""
        CODE_TRY_STATEMENT = """
try:
    a = 10
    a
except Exception:
    try:
        a
    finally:
        a
finally:
    a
"""
        self._testCode(CODE_TRY_STATEMENT, 4)