def test_valid_languages_bidi(self):
        for tag in self.valid_tags:
            with self.subTest(tag), self.settings(LANGUAGES_BIDI=[tag]):
                self.assertEqual(check_setting_languages_bidi(None), [])