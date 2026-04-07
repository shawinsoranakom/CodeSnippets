def test_basic_syntax20(self):
        """
        Fail silently when accessing a non-simple method
        """
        output = self.engine.render_to_string("basic-syntax20", {"var": SomeClass()})

        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")