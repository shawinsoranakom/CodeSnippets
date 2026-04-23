def test_nonascii_filenames(self):
        """
        Can find a file with non-ASCII character in an app static/ directory.
        """
        self.assertFileContains("test/⊗.txt", "⊗ in the app dir")