def test_basic_syntax04(self):
        """
        Fail silently when a variable is not found in the current context
        """
        output = self.engine.render_to_string("basic-syntax04")
        if self.engine.string_if_invalid:
            self.assertEqual(output, "asINVALIDdf")
        else:
            self.assertEqual(output, "asdf")