def test_inheritance29(self):
        """
        Inheritance from a template with a space in its name should work.
        """
        output = self.engine.render_to_string("inheritance29")
        self.assertEqual(output, "!")