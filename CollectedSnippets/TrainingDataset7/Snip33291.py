def test_i18n26(self):
        """
        translation of plural form with extra field in singular form (#13568)
        """
        output = self.engine.render_to_string(
            "i18n26", {"myextra_field": "test", "number": 1}
        )
        self.assertEqual(output, "singular test")