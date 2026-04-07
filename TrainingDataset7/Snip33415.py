def test_basic_syntax11(self):
        """
        Fail silently when a variable's attribute isn't found.
        """
        output = self.engine.render_to_string("basic-syntax11", {"var": SomeClass()})

        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")