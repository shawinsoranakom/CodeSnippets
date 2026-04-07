def test_multiple_locales_excluded(self):
        call_command("compilemessages", exclude=["it", "fr"], verbosity=0)
        self.assertTrue(os.path.exists(self.MO_FILE % "en"))
        self.assertFalse(os.path.exists(self.MO_FILE % "fr"))
        self.assertFalse(os.path.exists(self.MO_FILE % "it"))