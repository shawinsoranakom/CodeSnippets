def test_override_static_root(self):
        """
        Overriding the STATIC_ROOT setting should be reflected in the
        location attribute of
        django.contrib.staticfiles.storage.staticfiles_storage.
        """
        with self.settings(STATIC_ROOT="/tmp/test"):
            self.assertEqual(staticfiles_storage.location, os.path.abspath("/tmp/test"))