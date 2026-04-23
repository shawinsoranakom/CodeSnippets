def test_no_common_ignore_patterns(self):
        """
        With --no-default-ignore, common ignore patterns (*~, .*, CVS)
        are not ignored.
        """
        self.assertFileContains("test/.hidden", "should be ignored")
        self.assertFileContains("test/backup~", "should be ignored")
        self.assertFileContains("test/CVS", "should be ignored")