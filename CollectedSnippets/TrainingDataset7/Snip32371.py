def test_camelcase_filenames(self):
        """
        Can find a file with capital letters.
        """
        self.assertFileContains("test/camelCase.txt", "camelCase")