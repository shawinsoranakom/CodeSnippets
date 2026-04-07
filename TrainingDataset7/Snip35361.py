def test_override_staticfiles_dirs(self):
        """
        Overriding the STATICFILES_DIRS setting should be reflected in
        the locations attribute of the
        django.contrib.staticfiles.finders.FileSystemFinder instance.
        """
        finder = get_finder("django.contrib.staticfiles.finders.FileSystemFinder")
        test_path = "/tmp/test"
        expected_location = ("", test_path)
        self.assertNotIn(expected_location, finder.locations)
        with self.settings(STATICFILES_DIRS=[test_path]):
            finder = get_finder("django.contrib.staticfiles.finders.FileSystemFinder")
            self.assertIn(expected_location, finder.locations)