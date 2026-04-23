def test_file_iteration_with_windows_newline_at_chunk_boundary(self):
        f = File(BytesIO(b"one\r\ntwo\r\nthree"))
        # Set chunk size to create a boundary between \r and \n:
        # b'one\r\n...
        #        ^
        f.DEFAULT_CHUNK_SIZE = 4
        self.assertEqual(list(f), [b"one\r\n", b"two\r\n", b"three"])