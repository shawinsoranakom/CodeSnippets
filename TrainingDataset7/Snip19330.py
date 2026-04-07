def test_absolute_path(self):
        with self.settings(
            CACHES={
                "default": {
                    "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
                    "LOCATION": pathlib.Path.cwd() / "cache",
                },
            }
        ):
            self.assertEqual(check_file_based_cache_is_absolute(None), [])