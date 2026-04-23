def test_localized_language_info(self):
        li = get_language_info("de")
        self.assertEqual(li["code"], "de")
        self.assertEqual(li["name_local"], "Deutsch")
        self.assertEqual(li["name"], "German")
        self.assertIs(li["bidi"], False)