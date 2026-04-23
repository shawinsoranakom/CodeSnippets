def test_manifest_file_consistent_content(self):
        original_manifest_content = storage.staticfiles_storage.read_manifest()
        hashed_files = storage.staticfiles_storage.hashed_files
        # Force a change in the order of the hashed files.
        with mock.patch.object(
            storage.staticfiles_storage,
            "hashed_files",
            dict(reversed(hashed_files.items())),
        ):
            storage.staticfiles_storage.save_manifest()
        manifest_file_content = storage.staticfiles_storage.read_manifest()
        # The manifest file content should not change.
        self.assertEqual(original_manifest_content, manifest_file_content)