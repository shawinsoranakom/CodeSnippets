def test_inheritance05(self):
        """
        Two-level with double quotes instead of single quotes
        """
        output = self.engine.render_to_string("inheritance05")
        self.assertEqual(output, "1234")