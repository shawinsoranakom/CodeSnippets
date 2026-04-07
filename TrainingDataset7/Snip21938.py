def test_nonexistent_alias(self):
        msg = "Could not find config for 'nonexistent' in settings.STORAGES."
        storages = StorageHandler()
        with self.assertRaisesMessage(InvalidStorageError, msg):
            storages["nonexistent"]