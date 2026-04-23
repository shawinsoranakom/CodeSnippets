def test_one_locale_excluded(self):
        call_command("compilemessages", exclude=["it"], verbosity=0)
        self.assertTrue(os.path.exists(self.MO_FILE % "en"))
        self.assertTrue(os.path.exists(self.MO_FILE % "fr"))
        self.assertFalse(os.path.exists(self.MO_FILE % "it"))