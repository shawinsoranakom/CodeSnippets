def test_i18n38(self):
        with translation.override("cs"):
            output = self.engine.render_to_string("i18n38")
        self.assertEqual(output, "de: German/Deutsch/německy bidi=False")