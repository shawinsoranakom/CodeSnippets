def test_bcrypt(self):
        encoded = make_password("lètmein", hasher="bcrypt")
        self.assertTrue(is_password_usable(encoded))
        self.assertTrue(encoded.startswith("bcrypt$"))
        self.assertTrue(check_password("lètmein", encoded))
        self.assertFalse(check_password("lètmeinz", encoded))
        self.assertEqual(identify_hasher(encoded).algorithm, "bcrypt")
        # Blank passwords
        blank_encoded = make_password("", hasher="bcrypt")
        self.assertTrue(blank_encoded.startswith("bcrypt$"))
        self.assertTrue(is_password_usable(blank_encoded))
        self.assertTrue(check_password("", blank_encoded))
        self.assertFalse(check_password(" ", blank_encoded))