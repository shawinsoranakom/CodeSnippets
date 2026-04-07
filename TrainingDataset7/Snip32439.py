def test_ignore(self):
        """
        -i patterns are ignored.
        """
        self.assertFileNotFound("test/test.ignoreme")