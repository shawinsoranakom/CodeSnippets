def test_local_storage_detection_helper(self):
        staticfiles_storage = storage.staticfiles_storage
        try:
            storage.staticfiles_storage._wrapped = empty
            with self.settings(
                STORAGES={
                    **settings.STORAGES,
                    STATICFILES_STORAGE_ALIAS: {
                        "BACKEND": (
                            "django.contrib.staticfiles.storage.StaticFilesStorage"
                        )
                    },
                }
            ):
                command = collectstatic.Command()
                self.assertTrue(command.is_local_storage())

            storage.staticfiles_storage._wrapped = empty
            with self.settings(
                STORAGES={
                    **settings.STORAGES,
                    STATICFILES_STORAGE_ALIAS: {
                        "BACKEND": "staticfiles_tests.storage.DummyStorage"
                    },
                }
            ):
                command = collectstatic.Command()
                self.assertFalse(command.is_local_storage())

            collectstatic.staticfiles_storage = storage.FileSystemStorage()
            command = collectstatic.Command()
            self.assertTrue(command.is_local_storage())

            collectstatic.staticfiles_storage = DummyStorage()
            command = collectstatic.Command()
            self.assertFalse(command.is_local_storage())
        finally:
            staticfiles_storage._wrapped = empty
            collectstatic.staticfiles_storage = staticfiles_storage
            storage.staticfiles_storage = staticfiles_storage