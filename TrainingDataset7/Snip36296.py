def test_force_bytes_encoding(self):
        error_msg = "This is an exception, voilà".encode()
        result = force_bytes(error_msg, encoding="ascii", errors="ignore")
        self.assertEqual(result, b"This is an exception, voil")