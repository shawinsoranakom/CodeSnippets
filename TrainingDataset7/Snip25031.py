def test_multiple_locales_excluded_with_locale(self):
        management.call_command(
            "makemessages", locale=["en", "fr", "it"], exclude=["fr", "it"], verbosity=0
        )
        self.assertRecentlyModified(self.PO_FILE % "en")
        self.assertNotRecentlyModified(self.PO_FILE % "fr")
        self.assertNotRecentlyModified(self.PO_FILE % "it")