def test_ignores_based_on_pattern(self):
        call_command("compilemessages", ignore=["*/locale"], verbosity=0)
        self.assertAllExist("locale", ["en", "fr", "it"])
        self.assertNoneExist(self.CACHE_DIR, ["en", "fr", "it"])
        self.assertNoneExist(self.NESTED_DIR, ["en", "fr", "it"])