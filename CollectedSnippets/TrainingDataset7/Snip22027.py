def test_file_iteration_with_unix_newline_at_chunk_boundary(self):
        f = File(BytesIO(b"one\ntwo\nthree"))
        # Set chunk size to create a boundary after \n:
        # b'one\n...
        #        ^
        f.DEFAULT_CHUNK_SIZE = 4
        self.assertEqual(list(f), [b"one\n", b"two\n", b"three"])