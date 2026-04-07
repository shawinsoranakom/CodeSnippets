def test_i18n08(self):
        """translation of plural form"""
        output = self.engine.render_to_string("i18n08", {"number": 2})
        self.assertEqual(output, "2 plural")