def test_close(self):
        self.assertTrue(hasattr(cache, "close"))
        cache.close()