def test_filter_syntax23(self):
        """
        In attribute and dict lookups that raise an unexpected exception
        without a `silent_variable_attribute` set to True, the exception
        propagates
        """
        with self.assertRaises(SomeOtherException):
            self.engine.render_to_string("filter-syntax23", {"var": SomeClass()})