def test_override_media_url(self):
        """
        Overriding the MEDIA_URL setting should be reflected in the
        base_url attribute of django.core.files.storage.default_storage.
        """
        self.assertEqual(default_storage.base_location, "")
        with self.settings(MEDIA_URL="/test_value/"):
            self.assertEqual(default_storage.base_url, "/test_value/")