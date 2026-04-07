def test_override_staticfiles_storage(self):
        """
        Overriding the STORAGES setting should be reflected in
        the value of django.contrib.staticfiles.storage.staticfiles_storage.
        """
        new_class = "ManifestStaticFilesStorage"
        new_storage = "django.contrib.staticfiles.storage." + new_class
        with self.settings(
            STORAGES={STATICFILES_STORAGE_ALIAS: {"BACKEND": new_storage}}
        ):
            self.assertEqual(staticfiles_storage.__class__.__name__, new_class)