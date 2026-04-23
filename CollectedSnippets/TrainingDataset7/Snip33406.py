def test_basic_syntax01(self):
        """
        Plain text should go through the template parser untouched.
        """
        output = self.engine.render_to_string("basic-syntax01")
        self.assertEqual(output, "something cool")