def test_relative_path(self):
        with self.settings(
            CACHES={
                "default": {
                    "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
                    "LOCATION": "cache",
                },
            }
        ):
            self.assertEqual(
                check_file_based_cache_is_absolute(None),
                [
                    Warning(
                        "Your 'default' cache LOCATION path is relative. Use an "
                        "absolute path instead.",
                        id="caches.W003",
                    ),
                ],
            )