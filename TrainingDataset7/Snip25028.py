def test_one_locale_excluded(self):
        management.call_command("makemessages", exclude=["it"], verbosity=0)
        self.assertRecentlyModified(self.PO_FILE % "en")
        self.assertRecentlyModified(self.PO_FILE % "fr")
        self.assertNotRecentlyModified(self.PO_FILE % "it")