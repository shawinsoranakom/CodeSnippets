def test_missing_entry(self):
        missing_file_name = "cached/missing.css"
        configured_storage = storage.staticfiles_storage
        self.assertNotIn(missing_file_name, configured_storage.hashed_files)

        # File name not found in manifest
        with self.assertRaisesMessage(
            ValueError,
            "Missing staticfiles manifest entry for '%s'" % missing_file_name,
        ):
            self.hashed_file_path(missing_file_name)

        configured_storage.manifest_strict = False
        # File doesn't exist on disk
        err_msg = "The file '%s' could not be found with %r." % (
            missing_file_name,
            configured_storage._wrapped,
        )
        with self.assertRaisesMessage(ValueError, err_msg):
            self.hashed_file_path(missing_file_name)

        content = StringIO()
        content.write("Found")
        configured_storage.save(missing_file_name, content)
        # File exists on disk
        self.hashed_file_path(missing_file_name)