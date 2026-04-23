def test_multiple_locales_excluded(self):
        management.call_command("makemessages", exclude=["it", "fr"], verbosity=0)
        self.assertRecentlyModified(self.PO_FILE % "en")
        self.assertNotRecentlyModified(self.PO_FILE % "fr")
        self.assertNotRecentlyModified(self.PO_FILE % "it")