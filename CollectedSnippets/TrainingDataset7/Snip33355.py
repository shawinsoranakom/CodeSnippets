def test_i18n35(self):
        with translation.override("de"):
            output = self.engine.render_to_string("i18n35")
        self.assertEqual(output, "Seite nicht gefunden")