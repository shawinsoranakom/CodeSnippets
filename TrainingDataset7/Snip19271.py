def test_all(self):
        test_caches = CacheHandler(
            {
                "cache_1": {
                    "BACKEND": "django.core.cache.backends.dummy.DummyCache",
                },
                "cache_2": {
                    "BACKEND": "django.core.cache.backends.dummy.DummyCache",
                },
            }
        )
        self.assertEqual(test_caches.all(initialized_only=True), [])
        cache_1 = test_caches["cache_1"]
        self.assertEqual(test_caches.all(initialized_only=True), [cache_1])
        self.assertEqual(len(test_caches.all()), 2)
        # .all() initializes all caches.
        self.assertEqual(len(test_caches.all(initialized_only=True)), 2)
        self.assertEqual(test_caches.all(), test_caches.all(initialized_only=True))