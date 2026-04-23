def test_i18n29(self):
        output = self.engine.render_to_string("i18n29", {"LANGUAGE_CODE": "fi"})
        self.assertEqual(output, "fi: Finnish/suomi bidi=False")