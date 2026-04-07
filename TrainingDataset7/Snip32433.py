def test_all_files_more_verbose(self):
        """
        findstatic returns all candidate files if run without --first and -v2.
        Also, test that findstatic returns the searched locations with -v2.
        """
        result = call_command(
            "findstatic", "test/file.txt", verbosity=2, stdout=StringIO()
        )
        lines = [line.strip() for line in result.split("\n")]
        self.assertIn("project", lines[1])
        self.assertIn("apps", lines[2])
        self.assertIn("Looking in the following locations:", lines[3])
        searched_locations = ", ".join(lines[4:])
        # AppDirectoriesFinder searched locations
        self.assertIn(
            os.path.join("staticfiles_tests", "apps", "test", "static"),
            searched_locations,
        )
        self.assertIn(
            os.path.join("staticfiles_tests", "apps", "no_label", "static"),
            searched_locations,
        )
        # FileSystemFinder searched locations
        self.assertIn(TEST_SETTINGS["STATICFILES_DIRS"][1][1], searched_locations)
        self.assertIn(TEST_SETTINGS["STATICFILES_DIRS"][0], searched_locations)
        self.assertIn(str(TEST_SETTINGS["STATICFILES_DIRS"][2]), searched_locations)
        # DefaultStorageFinder searched locations
        self.assertIn(
            os.path.join("staticfiles_tests", "project", "site_media", "media"),
            searched_locations,
        )