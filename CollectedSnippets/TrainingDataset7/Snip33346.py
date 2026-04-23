def test_i18n01(self):
        """simple translation of a string delimited by '."""
        output = self.engine.render_to_string("i18n01")
        self.assertEqual(output, "xxxyyyxxx")