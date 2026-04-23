def test_redis_pool_options(self):
        pool = cache._cache._get_connection_pool(write=False)
        self.assertEqual(pool.connection_kwargs["db"], 5)
        self.assertEqual(pool.connection_kwargs["socket_timeout"], 0.1)
        self.assertIs(pool.connection_kwargs["retry_on_timeout"], True)