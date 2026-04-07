def test_staticfiles_dirs(self):
        """
        Can find a file in a STATICFILES_DIRS directory.
        """
        self.assertFileContains("test.txt", "Can we find")
        self.assertFileContains(os.path.join("prefix", "test.txt"), "Prefix")