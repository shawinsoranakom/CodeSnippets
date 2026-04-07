def test_unknown_language_code(self):
        with self.assertRaisesMessage(KeyError, "Unknown language code xx"):
            get_language_info("xx")
        with translation.override("xx"):
            # A language with no translation catalogs should fallback to the
            # untranslated string.
            self.assertEqual(gettext("Title"), "Title")