def test_from_module(self):
        self.assertIs(inspect.is_module_level_function(subprocess.run), True)
        self.assertIs(inspect.is_module_level_function(subprocess.check_output), True)
        self.assertIs(
            inspect.is_module_level_function(inspect.is_module_level_function), True
        )