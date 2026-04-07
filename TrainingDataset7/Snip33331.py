def test_i18n12(self):
        output = self.engine.render_to_string("i18n12")
        self.assertEqual(output, "de")