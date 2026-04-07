def test_clear_does_not_remove_cache_dir(self):
        cache.clear()
        self.assertTrue(
            os.path.exists(self.dirname), "Expected cache.clear to keep the cache dir"
        )