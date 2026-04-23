def test_docstring_is_ignored(self):
        """Test that docstrings don't print in the app"""
        CODE = """
def myfunc(a):
    '''This is the docstring'''
    return 42
"""
        self._testCode(CODE, 0)