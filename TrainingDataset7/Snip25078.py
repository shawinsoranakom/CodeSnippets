def test_language_bidi_null(self):
        self.assertIs(trans_null.get_language_bidi(), False)
        with override_settings(LANGUAGE_CODE="he"):
            self.assertIs(get_language_bidi(), True)