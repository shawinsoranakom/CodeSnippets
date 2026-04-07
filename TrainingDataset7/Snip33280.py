def test_i18n05(self):
        """simple translation of a string with interpolation"""
        output = self.engine.render_to_string("i18n05", {"anton": "yyy"})
        self.assertEqual(output, "xxxyyyxxx")