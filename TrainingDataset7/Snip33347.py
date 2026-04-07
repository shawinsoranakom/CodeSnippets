def test_i18n02(self):
        """simple translation of a string delimited by "."""
        output = self.engine.render_to_string("i18n02")
        self.assertEqual(output, "xxxyyyxxx")