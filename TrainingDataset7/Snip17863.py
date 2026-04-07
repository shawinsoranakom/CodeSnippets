def test_simple(self):
        encoded = make_password("lètmein")
        self.assertTrue(encoded.startswith("pbkdf2_sha256$"))
        self.assertTrue(is_password_usable(encoded))
        self.assertTrue(check_password("lètmein", encoded))
        self.assertFalse(check_password("lètmeinz", encoded))
        # Blank passwords
        blank_encoded = make_password("")
        self.assertTrue(blank_encoded.startswith("pbkdf2_sha256$"))
        self.assertTrue(is_password_usable(blank_encoded))
        self.assertTrue(check_password("", blank_encoded))
        self.assertFalse(check_password(" ", blank_encoded))