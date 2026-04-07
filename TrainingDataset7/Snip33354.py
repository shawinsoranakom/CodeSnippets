def test_i18n25(self):
        with translation.override("de"):
            output = self.engine.render_to_string(
                "i18n25", {"somevar": "Page not found"}
            )
        self.assertEqual(output, "SEITE NICHT GEFUNDEN")