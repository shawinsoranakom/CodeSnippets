def test_staticfiles_dirs_priority(self):
        """
        File in STATICFILES_DIRS has priority over file in app.
        """
        self.assertFileContains("test/file.txt", "STATICFILES_DIRS")