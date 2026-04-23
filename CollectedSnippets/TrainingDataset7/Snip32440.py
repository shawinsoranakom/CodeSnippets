def test_common_ignore_patterns(self):
        """
        Common ignore patterns (*~, .*, CVS) are ignored.
        """
        self.assertFileNotFound("test/.hidden")
        self.assertFileNotFound("test/backup~")
        self.assertFileNotFound("test/CVS")