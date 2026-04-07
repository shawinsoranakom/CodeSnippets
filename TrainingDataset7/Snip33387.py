def test_i18n16(self):
        with translation.override("de"):
            output = self.engine.render_to_string("i18n16")
        self.assertEqual(output, "<")