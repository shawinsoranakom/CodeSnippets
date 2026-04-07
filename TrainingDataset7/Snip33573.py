def test_inheritance42(self):
        """
        Expression starting and ending with a quote
        """
        output = self.engine.render_to_string("inheritance42")
        self.assertEqual(output, "1234")