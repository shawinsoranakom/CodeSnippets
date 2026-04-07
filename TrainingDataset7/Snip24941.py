def setUp(self):
        super().setUp()
        copytree("canned_locale", "locale")
        copytree("canned_locale", self.CACHE_DIR)
        copytree("canned_locale", self.NESTED_DIR)