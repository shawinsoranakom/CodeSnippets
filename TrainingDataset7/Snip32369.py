def test_app_files(self):
        """
        Can find a file in an app static/ directory.
        """
        self.assertFileContains("test/file1.txt", "file1 in the app dir")