def test_clear_empties_manifest(self):
        cleared_file_name = storage.staticfiles_storage.clean_name(
            os.path.join("test", "cleared.txt")
        )
        # collect the additional file
        self.run_collectstatic()

        hashed_files = storage.staticfiles_storage.hashed_files
        self.assertIn(cleared_file_name, hashed_files)

        manifest_content, _ = storage.staticfiles_storage.load_manifest()
        self.assertIn(cleared_file_name, manifest_content)

        original_path = storage.staticfiles_storage.path(cleared_file_name)
        self.assertTrue(os.path.exists(original_path))

        # delete the original file form the app, collect with clear
        os.unlink(self._clear_filename)
        self.run_collectstatic(clear=True)

        self.assertFileNotFound(original_path)

        hashed_files = storage.staticfiles_storage.hashed_files
        self.assertNotIn(cleared_file_name, hashed_files)

        manifest_content, _ = storage.staticfiles_storage.load_manifest()
        self.assertNotIn(cleared_file_name, manifest_content)