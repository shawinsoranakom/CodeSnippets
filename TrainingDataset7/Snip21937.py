def test_defaults(self):
        storages = StorageHandler()
        self.assertEqual(
            storages.backends,
            {
                DEFAULT_STORAGE_ALIAS: {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                },
                STATICFILES_STORAGE_ALIAS: {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
                },
            },
        )