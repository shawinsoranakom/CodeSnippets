def test_translation_loading(self):
        """
        "loading_app" does not have translations for all languages provided by
        "loading". Catalogs are merged correctly.
        """
        tests = [
            ("en", "local country person"),
            ("en_AU", "aussie"),
            ("en_NZ", "kiwi"),
            ("en_CA", "canuck"),
        ]
        # Load all relevant translations.
        for language, _ in tests:
            activate(language)
        # Catalogs are merged correctly.
        for language, nickname in tests:
            with self.subTest(language=language):
                activate(language)
                self.assertEqual(gettext("local country person"), nickname)