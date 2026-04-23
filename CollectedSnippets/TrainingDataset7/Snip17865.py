def test_bytes(self):
        encoded = make_password(b"bytes_password")
        self.assertTrue(encoded.startswith("pbkdf2_sha256$"))
        self.assertIs(is_password_usable(encoded), True)
        self.assertIs(check_password(b"bytes_password", encoded), True)