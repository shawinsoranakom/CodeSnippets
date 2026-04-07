def test_unknown_only_country_code(self):
        li = get_language_info("de-xx")
        self.assertEqual(li["code"], "de")
        self.assertEqual(li["name_local"], "Deutsch")
        self.assertEqual(li["name"], "German")
        self.assertIs(li["bidi"], False)