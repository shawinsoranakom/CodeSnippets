def test_function_call_statement(self):
        """Test with function calls"""
        CODE_FUNCTION_CALL = """
def myfunc(a):
    a
a =10
myfunc(a)
"""
        self._testCode(CODE_FUNCTION_CALL, 1)