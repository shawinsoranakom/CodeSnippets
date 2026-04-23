def test_filter_syntax14(self):
        """
        In methods that raise an exception without a
        `silent_variable_attribute` set to True, the exception propagates
        """
        with self.assertRaises(SomeOtherException):
            self.engine.render_to_string("filter-syntax14", {"var": SomeClass()})