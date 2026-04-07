def test_override_file_upload_permissions(self):
        """
        Overriding the FILE_UPLOAD_PERMISSIONS setting should be reflected in
        the file_permissions_mode attribute of
        django.core.files.storage.default_storage.
        """
        self.assertEqual(default_storage.file_permissions_mode, 0o644)
        with self.settings(FILE_UPLOAD_PERMISSIONS=0o777):
            self.assertEqual(default_storage.file_permissions_mode, 0o777)