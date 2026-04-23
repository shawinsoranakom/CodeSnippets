def test_get_connection_pool(self):
        pool = cache._cache._get_connection_pool(write=True)
        self.assertIsInstance(pool, self.lib.ConnectionPool)

        pool = cache._cache._get_connection_pool(write=False)
        self.assertIsInstance(pool, self.lib.ConnectionPool)