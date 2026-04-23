def test_one_locale_excluded_with_locale(self):
        call_command(
            "compilemessages", locale=["en", "fr"], exclude=["fr"], verbosity=0
        )
        self.assertTrue(os.path.exists(self.MO_FILE % "en"))
        self.assertFalse(os.path.exists(self.MO_FILE % "fr"))
        self.assertFalse(os.path.exists(self.MO_FILE % "it"))