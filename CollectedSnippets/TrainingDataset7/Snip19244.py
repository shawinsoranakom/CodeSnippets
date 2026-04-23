def setUp(self):
        self.default_cache = caches["default"]
        self.addCleanup(self.default_cache.clear)
        self.other_cache = caches["other"]
        self.addCleanup(self.other_cache.clear)