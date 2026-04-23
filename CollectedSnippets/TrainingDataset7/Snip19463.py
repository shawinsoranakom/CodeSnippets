def test_inconsistent_language_settings(self):
        msg = (
            "You have provided a value for the LANGUAGE_CODE setting that is "
            "not in the LANGUAGES setting."
        )
        for tag in ["fr", "fr-CA", "fr-357"]:
            with self.subTest(tag), self.settings(LANGUAGE_CODE=tag):
                self.assertEqual(
                    check_language_settings_consistent(None),
                    [
                        Error(msg, id="translation.E004"),
                    ],
                )