def test_close_only_initialized(self):
        with self.settings(
            CACHES={
                "cache_1": {
                    "BACKEND": "cache.closeable_cache.CacheClass",
                },
                "cache_2": {
                    "BACKEND": "cache.closeable_cache.CacheClass",
                },
            }
        ):
            self.assertEqual(caches.all(initialized_only=True), [])
            signals.request_finished.send(self.__class__)
            self.assertEqual(caches.all(initialized_only=True), [])