def test_manifest_does_not_exist(self):
        storage.staticfiles_storage.manifest_name = "does.not.exist.json"
        self.assertIsNone(storage.staticfiles_storage.read_manifest())