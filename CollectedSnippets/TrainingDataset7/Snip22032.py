def test_writable(self):
        with (
            tempfile.TemporaryFile() as temp,
            File(temp, name="something.txt") as test_file,
        ):
            self.assertTrue(test_file.writable())
        self.assertFalse(test_file.writable())
        with (
            tempfile.TemporaryFile("rb") as temp,
            File(temp, name="something.txt") as test_file,
        ):
            self.assertFalse(test_file.writable())