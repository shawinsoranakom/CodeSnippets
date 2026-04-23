def test_i18n37(self):
        with translation.override("de"):
            output = self.engine.render_to_string("i18n37")
        self.assertEqual(output, "Error: Seite nicht gefunden")