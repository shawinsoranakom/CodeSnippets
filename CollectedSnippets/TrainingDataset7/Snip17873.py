def test_unusable(self):
        encoded = make_password(None)
        self.assertEqual(
            len(encoded),
            len(UNUSABLE_PASSWORD_PREFIX) + UNUSABLE_PASSWORD_SUFFIX_LENGTH,
        )
        self.assertFalse(is_password_usable(encoded))
        self.assertFalse(check_password(None, encoded))
        self.assertFalse(check_password(encoded, encoded))
        self.assertFalse(check_password(UNUSABLE_PASSWORD_PREFIX, encoded))
        self.assertFalse(check_password("", encoded))
        self.assertFalse(check_password("lètmein", encoded))
        self.assertFalse(check_password("lètmeinz", encoded))
        with self.assertRaisesMessage(ValueError, "Unknown password hashing algorithm"):
            identify_hasher(encoded)
        # Assert that the unusable passwords actually contain a random part.
        # This might fail one day due to a hash collision.
        self.assertNotEqual(encoded, make_password(None), "Random password collision?")