def test_i18n24(self):
        with translation.override("de"):
            output = self.engine.render_to_string("i18n24")
        self.assertEqual(output, "SEITE NICHT GEFUNDEN")