def test_inheritance27(self):
        """
        Inheritance from a template that doesn't have any blocks
        """
        output = self.engine.render_to_string("inheritance27")
        self.assertEqual(output, "no tags")