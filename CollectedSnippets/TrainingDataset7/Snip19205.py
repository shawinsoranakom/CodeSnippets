def test_cache_client_class(self):
        self.assertIs(cache._class, RedisCacheClient)
        self.assertIsInstance(cache._cache, RedisCacheClient)