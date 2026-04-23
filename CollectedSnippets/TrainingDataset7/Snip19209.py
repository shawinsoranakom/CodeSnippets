def test_get_client(self):
        self.assertIsInstance(cache._cache.get_client(), self.lib.Redis)