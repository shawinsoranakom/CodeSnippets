def test_invalid_languages(self):
        msg = "You have provided an invalid language code in the LANGUAGES setting: %r."
        for tag in self.invalid_tags:
            with self.subTest(tag), self.settings(LANGUAGES=[(tag, tag)]):
                self.assertEqual(
                    check_setting_languages(None),
                    [
                        Error(msg % tag, id="translation.E002"),
                    ],
                )