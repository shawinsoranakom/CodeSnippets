def test_guesses_content_type_on_file_encoding(self):
        self.assertEqual(
            b"Content-Type: application/octet-stream",
            encode_file("IGNORE", "IGNORE", DummyFile("file.bin"))[2],
        )
        self.assertEqual(
            b"Content-Type: text/plain",
            encode_file("IGNORE", "IGNORE", DummyFile("file.txt"))[2],
        )
        self.assertIn(
            encode_file("IGNORE", "IGNORE", DummyFile("file.zip"))[2],
            (
                b"Content-Type: application/x-compress",
                b"Content-Type: application/x-zip",
                b"Content-Type: application/x-zip-compressed",
                b"Content-Type: application/zip",
            ),
        )
        self.assertEqual(
            b"Content-Type: application/octet-stream",
            encode_file("IGNORE", "IGNORE", DummyFile("file.unknown"))[2],
        )