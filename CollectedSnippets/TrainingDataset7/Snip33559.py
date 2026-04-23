def test_inheritance_28(self):
        """
        Set up a base template with a space in it.
        """
        output = self.engine.render_to_string("inheritance 28")
        self.assertEqual(output, "!")