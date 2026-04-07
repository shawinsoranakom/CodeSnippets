def test_pymemcache_options(self):
        self.assertIs(cache._cache.default_kwargs["no_delay"], True)