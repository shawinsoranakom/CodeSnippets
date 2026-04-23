def test_coroutine(self):
        self.assertIs(inspect.is_module_level_function(aget_object_or_404), True)