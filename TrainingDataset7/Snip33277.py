def test_i18n03(self):
        """simple translation of a variable"""
        output = self.engine.render_to_string("i18n03", {"anton": "Å"})
        self.assertEqual(output, "Å")