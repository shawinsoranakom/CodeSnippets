def test_valid_languages(self):
        for tag in self.valid_tags:
            with self.subTest(tag), self.settings(LANGUAGES=[(tag, tag)]):
                self.assertEqual(check_setting_languages(None), [])