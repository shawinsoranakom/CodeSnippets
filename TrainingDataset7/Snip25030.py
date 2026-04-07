def test_one_locale_excluded_with_locale(self):
        management.call_command(
            "makemessages", locale=["en", "fr"], exclude=["fr"], verbosity=0
        )
        self.assertRecentlyModified(self.PO_FILE % "en")
        self.assertNotRecentlyModified(self.PO_FILE % "fr")
        self.assertNotRecentlyModified(self.PO_FILE % "it")