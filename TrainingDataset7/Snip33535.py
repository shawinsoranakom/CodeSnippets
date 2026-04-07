def test_inheritance04(self):
        """
        Two-level with no redefinitions on second level
        """
        output = self.engine.render_to_string("inheritance04")
        self.assertEqual(output, "1&3_")