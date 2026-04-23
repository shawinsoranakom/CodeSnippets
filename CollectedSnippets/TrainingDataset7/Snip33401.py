def test_autoescape_literals01(self):
        """
        Literal strings are safe.
        """
        output = self.engine.render_to_string("autoescape-literals01")
        self.assertEqual(output, "this & that")