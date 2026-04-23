def test_nonexistent_backend(self):
        test_caches = CacheHandler(
            {
                "invalid_backend": {
                    "BACKEND": "django.nonexistent.NonexistentBackend",
                },
            }
        )
        msg = (
            "Could not find backend 'django.nonexistent.NonexistentBackend': "
            "No module named 'django.nonexistent'"
        )
        with self.assertRaisesMessage(InvalidCacheBackendError, msg):
            test_caches["invalid_backend"]