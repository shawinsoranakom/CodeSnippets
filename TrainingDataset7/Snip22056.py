def test_file_move_overwrite(self):
        handle_a, self.file_a = tempfile.mkstemp()
        handle_b, self.file_b = tempfile.mkstemp()

        # file_move_safe() raises FileExistsError if the destination file
        # exists and allow_overwrite is False.
        msg = r"Destination file .* exists and allow_overwrite is False\."
        with self.assertRaisesRegex(FileExistsError, msg):
            file_move_safe(self.file_a, self.file_b, allow_overwrite=False)

        # should allow it and continue on if allow_overwrite is True
        self.assertIsNone(
            file_move_safe(self.file_a, self.file_b, allow_overwrite=True)
        )

        os.close(handle_a)
        os.close(handle_b)