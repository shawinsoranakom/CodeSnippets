def test_filename_with_percent_sign(self):
        self.assertFileContains("test/%2F.txt", "%2F content")