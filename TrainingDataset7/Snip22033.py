def test_seekable(self):
        with (
            tempfile.TemporaryFile() as temp,
            File(temp, name="something.txt") as test_file,
        ):
            self.assertTrue(test_file.seekable())
        self.assertFalse(test_file.seekable())