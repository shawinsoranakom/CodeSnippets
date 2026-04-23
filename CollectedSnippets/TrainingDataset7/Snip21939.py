def test_nonexistent_backend(self):
        test_storages = StorageHandler(
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
        with self.assertRaisesMessage(InvalidStorageError, msg):
            test_storages["invalid_backend"]