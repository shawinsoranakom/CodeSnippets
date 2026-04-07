def test_default_lang_without_prefix(self):
        """
        With i18n_patterns(..., prefix_default_language=False), the default
        language (settings.LANGUAGE_CODE) should be accessible without a
        prefix.
        """
        response = self.client.get("/simple/")
        self.assertEqual(response.content, b"Yes")