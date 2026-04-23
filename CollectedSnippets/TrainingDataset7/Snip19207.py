def test_get_connection_pool_index(self):
        pool_index = cache._cache._get_connection_pool_index(write=True)
        self.assertEqual(pool_index, 0)
        pool_index = cache._cache._get_connection_pool_index(write=False)
        if len(cache._cache._servers) == 1:
            self.assertEqual(pool_index, 0)
        else:
            self.assertGreater(pool_index, 0)
            self.assertLess(pool_index, len(cache._cache._servers))