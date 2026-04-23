def test_has_key(self):
        # The cache can be inspected for cache keys
        cache.set("hello1", "goodbye1")
        self.assertIs(cache.has_key("hello1"), True)
        self.assertIs(cache.has_key("goodbye1"), False)
        cache.set("no_expiry", "here", None)
        self.assertIs(cache.has_key("no_expiry"), True)
        cache.set("null", None)
        self.assertIs(cache.has_key("null"), True)