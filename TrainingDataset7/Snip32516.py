def test_manifest_exists(self):
        filename = storage.staticfiles_storage.manifest_name
        path = storage.staticfiles_storage.path(filename)
        self.assertTrue(os.path.exists(path))