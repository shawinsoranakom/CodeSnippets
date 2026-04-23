def test_filter_syntax22(self):
        """
        Fail silently for non-callable attribute and dict lookups which
        raise an exception with a `silent_variable_failure` attribute
        """
        output = self.engine.render_to_string("filter-syntax22", {"var": SomeClass()})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "1INVALID2")
        else:
            self.assertEqual(output, "12")