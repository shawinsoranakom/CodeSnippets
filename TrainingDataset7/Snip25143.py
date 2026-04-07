def test_check_for_language_null(self):
        self.assertIs(trans_null.check_for_language("en"), True)