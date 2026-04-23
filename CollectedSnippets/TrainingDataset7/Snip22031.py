def test_readable(self):
        with (
            tempfile.TemporaryFile() as temp,
            File(temp, name="something.txt") as test_file,
        ):
            self.assertTrue(test_file.readable())
        self.assertFalse(test_file.readable())