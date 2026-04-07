def test_i18n36(self):
        with translation.override("de"):
            output = self.engine.render_to_string("i18n36")
        self.assertEqual(output, "Page not found")