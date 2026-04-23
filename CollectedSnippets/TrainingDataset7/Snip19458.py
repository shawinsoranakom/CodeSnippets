def test_invalid_language_code(self):
        msg = "You have provided an invalid value for the LANGUAGE_CODE setting: %r."
        for tag in self.invalid_tags:
            with self.subTest(tag), self.settings(LANGUAGE_CODE=tag):
                self.assertEqual(
                    check_setting_language_code(None),
                    [
                        Error(msg % tag, id="translation.E001"),
                    ],
                )