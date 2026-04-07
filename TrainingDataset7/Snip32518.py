def test_manifest_does_not_ignore_permission_error(self):
        with mock.patch("builtins.open", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                storage.staticfiles_storage.read_manifest()