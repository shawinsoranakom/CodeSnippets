def test_i18n_asvar_safestring(self):
        context = {"title": "<Main Title>"}
        output = self.engine.render_to_string("i18n_asvar_safestring", context=context)
        self.assertEqual(output, "&lt;Main Title&gt;other text")