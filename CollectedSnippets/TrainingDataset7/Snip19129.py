def test_cache_versioning_has_key(self):
        cache.set("answer1", 42)

        # has_key
        self.assertIs(cache.has_key("answer1"), True)
        self.assertIs(cache.has_key("answer1", version=1), True)
        self.assertIs(cache.has_key("answer1", version=2), False)

        self.assertIs(caches["v2"].has_key("answer1"), False)
        self.assertIs(caches["v2"].has_key("answer1", version=1), True)
        self.assertIs(caches["v2"].has_key("answer1", version=2), False)