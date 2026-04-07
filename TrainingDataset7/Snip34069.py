def test_widthratio15(self):
        """
        Test whitespace in filter argument
        """
        output = self.engine.render_to_string("widthratio15", {"a": 50, "b": 100})
        self.assertEqual(output, "0")