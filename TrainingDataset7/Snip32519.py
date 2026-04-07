def test_loaded_cache(self):
        self.assertNotEqual(storage.staticfiles_storage.hashed_files, {})
        manifest_content = storage.staticfiles_storage.read_manifest()
        self.assertIn(
            '"version": "%s"' % storage.staticfiles_storage.manifest_version,
            manifest_content,
        )