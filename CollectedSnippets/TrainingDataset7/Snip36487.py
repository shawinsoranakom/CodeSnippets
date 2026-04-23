def test_class_and_static_method(self):
        self.assertIs(inspect.is_module_level_function(self._static_method), True)
        self.assertIs(inspect.is_module_level_function(self._class_method), False)