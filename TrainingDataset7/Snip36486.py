def test_lambda(self):
        self.assertIs(inspect.is_module_level_function(lambda: True), False)