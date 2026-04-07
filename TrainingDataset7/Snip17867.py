def test_pbkdf2(self):
        encoded = make_password("lètmein", "seasalt", "pbkdf2_sha256")
        self.assertEqual(
            encoded,
            "pbkdf2_sha256$1500000$"
            "seasalt$P4UiMPVduVWIL/oS1GzH+IofsccjJNM5hUTikBvi5to=",
        )
        self.assertTrue(is_password_usable(encoded))
        self.assertTrue(check_password("lètmein", encoded))
        self.assertFalse(check_password("lètmeinz", encoded))
        self.assertEqual(identify_hasher(encoded).algorithm, "pbkdf2_sha256")
        # Blank passwords
        blank_encoded = make_password("", "seasalt", "pbkdf2_sha256")
        self.assertTrue(blank_encoded.startswith("pbkdf2_sha256$"))
        self.assertTrue(is_password_usable(blank_encoded))
        self.assertTrue(check_password("", blank_encoded))
        self.assertFalse(check_password(" ", blank_encoded))
        # Salt entropy check.
        hasher = get_hasher("pbkdf2_sha256")
        encoded_weak_salt = make_password("lètmein", "iodizedsalt", "pbkdf2_sha256")
        encoded_strong_salt = make_password("lètmein", hasher.salt(), "pbkdf2_sha256")
        self.assertIs(hasher.must_update(encoded_weak_salt), True)
        self.assertIs(hasher.must_update(encoded_strong_salt), False)