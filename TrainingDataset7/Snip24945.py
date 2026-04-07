def test_multiple_locale_dirs_ignored(self):
        call_command(
            "compilemessages", ignore=["cache/locale", "outdated"], verbosity=0
        )
        self.assertAllExist("locale", ["en", "fr", "it"])
        self.assertNoneExist(self.CACHE_DIR, ["en", "fr", "it"])
        self.assertNoneExist(self.NESTED_DIR, ["en", "fr", "it"])