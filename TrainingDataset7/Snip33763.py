def test_if_tag_badarg01(self):
        """Nonexistent args"""
        output = self.engine.render_to_string("if-tag-badarg01")
        self.assertEqual(output, "")