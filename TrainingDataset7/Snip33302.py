def test_i18n40(self):
        output = self.engine.render_to_string("i18n40")
        self.assertEqual(output, "")