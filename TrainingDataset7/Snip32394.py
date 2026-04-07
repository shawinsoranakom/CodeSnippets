def test_nonexistent_directories(self):
        with self.settings(
            STATICFILES_DIRS=[
                "/fake/path",
                ("prefix", "/fake/prefixed/path"),
            ]
        ):
            self.assertEqual(
                check_finders(None),
                [
                    Warning(
                        "The directory '/fake/path' in the STATICFILES_DIRS "
                        "setting does not exist.",
                        id="staticfiles.W004",
                    ),
                    Warning(
                        "The directory '/fake/prefixed/path' in the "
                        "STATICFILES_DIRS setting does not exist.",
                        id="staticfiles.W004",
                    ),
                ],
            )
            # Nonexistent directories are skipped.
            finder = get_finder("django.contrib.staticfiles.finders.FileSystemFinder")
            self.assertEqual(list(finder.list(None)), [])