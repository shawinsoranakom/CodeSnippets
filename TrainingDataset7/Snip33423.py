def test_basic_syntax19(self):
        """
        Fail silently when a variable's dictionary key isn't found.
        """
        output = self.engine.render_to_string("basic-syntax19", {"foo": {"bar": "baz"}})

        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")