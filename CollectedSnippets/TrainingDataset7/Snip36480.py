def test_builtin(self):
        self.assertIs(inspect.is_module_level_function(any), False)
        self.assertIs(inspect.is_module_level_function(isinstance), False)