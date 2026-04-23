def test_one_locale_dir_ignored(self):
        call_command("compilemessages", ignore=["cache"], verbosity=0)
        self.assertAllExist("locale", ["en", "fr", "it"])
        self.assertNoneExist(self.CACHE_DIR, ["en", "fr", "it"])
        self.assertAllExist(self.NESTED_DIR, ["en", "fr", "it"])