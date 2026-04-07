def test_file_iteration_with_mac_newline_at_chunk_boundary(self):
        f = File(BytesIO(b"one\rtwo\rthree"))
        # Set chunk size to create a boundary after \r:
        # b'one\r...
        #        ^
        f.DEFAULT_CHUNK_SIZE = 4
        self.assertEqual(list(f), [b"one\r", b"two\r", b"three"])