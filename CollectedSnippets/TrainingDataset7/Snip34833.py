def test_file_encoding(self):
        encoded_file = encode_file(
            "TEST_BOUNDARY", "TEST_KEY", DummyFile("test_name.bin")
        )
        self.assertEqual(b"--TEST_BOUNDARY", encoded_file[0])
        self.assertEqual(
            b'Content-Disposition: form-data; name="TEST_KEY"; '
            b'filename="test_name.bin"',
            encoded_file[1],
        )
        self.assertEqual(b"TEST_FILE_CONTENT", encoded_file[-1])