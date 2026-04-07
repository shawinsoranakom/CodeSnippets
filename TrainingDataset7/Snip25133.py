def test_unknown_language_code_and_country_code(self):
        with self.assertRaisesMessage(KeyError, "Unknown language code xx-xx and xx"):
            get_language_info("xx-xx")