def test_parse_cache(self):
        hashed_files = storage.staticfiles_storage.hashed_files
        manifest, _ = storage.staticfiles_storage.load_manifest()
        self.assertEqual(hashed_files, manifest)