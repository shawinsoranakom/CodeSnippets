def test_i18n28_2(self):
        output = self.engine.render_to_string("i18n28_2")
        self.assertEqual(output, "de: German/Deutsch bidi=False")