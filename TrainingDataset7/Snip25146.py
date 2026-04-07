def test_get_language_from_request_null(self):
        lang = trans_null.get_language_from_request(None)
        self.assertEqual(lang, "en")
        with override_settings(LANGUAGE_CODE="de"):
            lang = trans_null.get_language_from_request(None)
            self.assertEqual(lang, "de")