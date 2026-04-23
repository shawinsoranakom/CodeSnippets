def test_i18n06(self):
        """simple translation of a string to German"""
        with translation.override("de"):
            output = self.engine.render_to_string("i18n06")
        self.assertEqual(output, "Seite nicht gefunden")