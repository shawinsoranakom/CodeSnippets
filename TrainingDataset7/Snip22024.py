def test_file_iteration_windows_newlines(self):
        """
        #8149 - File objects with \r\n line endings should yield lines
        when iterated over.
        """
        f = File(BytesIO(b"one\r\ntwo\r\nthree"))
        self.assertEqual(list(f), [b"one\r\n", b"two\r\n", b"three"])