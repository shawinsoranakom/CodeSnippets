def test_basic_syntax18(self):
        """
        Attribute syntax allows a template to call a dictionary key's
        value.
        """
        output = self.engine.render_to_string("basic-syntax18", {"foo": {"bar": "baz"}})
        self.assertEqual(output, "baz")