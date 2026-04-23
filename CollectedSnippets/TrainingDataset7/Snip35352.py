def test_override_media_root(self):
        """
        Overriding the MEDIA_ROOT setting should be reflected in the
        base_location attribute of django.core.files.storage.default_storage.
        """
        self.assertEqual(default_storage.base_location, "")
        with self.settings(MEDIA_ROOT="test_value"):
            self.assertEqual(default_storage.base_location, "test_value")