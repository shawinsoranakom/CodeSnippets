def test_read_manifest_nonexistent(self):
        os.remove(self.manifest_file)
        self.assertIsNone(self.staticfiles_storage.read_manifest())