def test_pylibmc_options(self):
        self.assertTrue(cache._cache.binary)
        self.assertEqual(cache._cache.behaviors["tcp_nodelay"], int(True))