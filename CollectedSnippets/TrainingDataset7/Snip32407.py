def test_get_finder(self):
        self.assertIsInstance(
            finders.get_finder("django.contrib.staticfiles.finders.FileSystemFinder"),
            finders.FileSystemFinder,
        )