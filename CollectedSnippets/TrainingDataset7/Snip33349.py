def test_i18n09(self):
        """simple non-translation (only marking) of a string to German"""
        with translation.override("de"):
            output = self.engine.render_to_string("i18n09")
        self.assertEqual(output, "Page not found")