def test_method(self):
        self.assertIs(inspect.is_module_level_function(self.test_method), False)
        self.assertIs(inspect.is_module_level_function(self.setUp), False)