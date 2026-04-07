def test_i18n27(self):
        """translation of singular form in Russian (#14126)"""
        with translation.override("ru"):
            output = self.engine.render_to_string("i18n27", {"number": 1})
        self.assertEqual(
            output, "1 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442"
        )