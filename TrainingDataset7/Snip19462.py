def test_invalid_languages_bidi(self):
        msg = (
            "You have provided an invalid language code in the LANGUAGES_BIDI setting: "
            "%r."
        )
        for tag in self.invalid_tags:
            with self.subTest(tag), self.settings(LANGUAGES_BIDI=[tag]):
                self.assertEqual(
                    check_setting_languages_bidi(None),
                    [
                        Error(msg % tag, id="translation.E003"),
                    ],
                )