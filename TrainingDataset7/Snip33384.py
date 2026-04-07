def test_i18n13(self):
        with translation.override("de"):
            output = self.engine.render_to_string("i18n13")
        self.assertEqual(output, "Passwort")