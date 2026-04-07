def test_override_static_url(self):
        """
        Overriding the STATIC_URL setting should be reflected in the
        base_url attribute of
        django.contrib.staticfiles.storage.staticfiles_storage.
        """
        with self.settings(STATIC_URL="/test/"):
            self.assertEqual(staticfiles_storage.base_url, "/test/")