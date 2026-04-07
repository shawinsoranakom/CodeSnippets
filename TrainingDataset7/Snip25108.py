def test_english_fallback(self):
        """
        With a non-English LANGUAGE_CODE and if the active language is English
        or one of its variants, the untranslated string should be returned
        (instead of falling back to LANGUAGE_CODE) (See #24413).
        """
        self.assertEqual(gettext("Image"), "Bild")
        with translation.override("en"):
            self.assertEqual(gettext("Image"), "Image")
        with translation.override("en-us"):
            self.assertEqual(gettext("Image"), "Image")
        with translation.override("en-ca"):
            self.assertEqual(gettext("Image"), "Image")