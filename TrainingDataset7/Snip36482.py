def test_private_function(self):
        def private_function():
            pass

        self.assertIs(inspect.is_module_level_function(private_function), False)