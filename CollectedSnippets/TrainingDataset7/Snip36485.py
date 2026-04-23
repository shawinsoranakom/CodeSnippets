def test_unbound_method(self):
        self.assertIs(
            inspect.is_module_level_function(self.__class__.test_unbound_method), True
        )
        self.assertIs(inspect.is_module_level_function(self.__class__.setUp), True)