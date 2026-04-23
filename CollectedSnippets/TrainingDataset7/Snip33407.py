def test_basic_syntax02(self):
        """
        Variables should be replaced with their value in the current
        context
        """
        output = self.engine.render_to_string("basic-syntax02", {"headline": "Success"})
        self.assertEqual(output, "Success")