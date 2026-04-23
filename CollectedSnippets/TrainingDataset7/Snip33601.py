def test_filter_syntax24(self):
        """
        In attribute and dict lookups that raise an unexpected exception
        without a `silent_variable_attribute` set to True, the exception
        propagates
        """
        with self.assertRaises(SomeOtherException):
            self.engine.render_to_string("filter-syntax24", {"var": SomeClass()})