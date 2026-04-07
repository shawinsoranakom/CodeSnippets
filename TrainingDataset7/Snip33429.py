def test_basic_syntax24(self):
        """
        Embedded newlines make it not-a-tag.
        """
        output = self.engine.render_to_string("basic-syntax24")
        self.assertEqual(output, "{{ moo\n }}")