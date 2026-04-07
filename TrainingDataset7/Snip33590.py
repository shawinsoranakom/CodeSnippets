def test_filter_syntax13(self):
        """
        Fail silently for methods that raise an exception with a
        `silent_variable_failure` attribute
        """
        output = self.engine.render_to_string("filter-syntax13", {"var": SomeClass()})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "1INVALID2")
        else:
            self.assertEqual(output, "12")