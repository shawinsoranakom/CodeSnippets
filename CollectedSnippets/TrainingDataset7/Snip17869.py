def test_bcrypt_sha256(self):
        encoded = make_password("lètmein", hasher="bcrypt_sha256")
        self.assertTrue(is_password_usable(encoded))
        self.assertTrue(encoded.startswith("bcrypt_sha256$"))
        self.assertTrue(check_password("lètmein", encoded))
        self.assertFalse(check_password("lètmeinz", encoded))
        self.assertEqual(identify_hasher(encoded).algorithm, "bcrypt_sha256")

        # password truncation no longer works
        password = (
            "VSK0UYV6FFQVZ0KG88DYN9WADAADZO1CTSIVDJUNZSUML6IBX7LN7ZS3R5"
            "JGB3RGZ7VI7G7DJQ9NI8BQFSRPTG6UWTTVESA5ZPUN"
        )
        encoded = make_password(password, hasher="bcrypt_sha256")
        self.assertTrue(check_password(password, encoded))
        self.assertFalse(check_password(password[:72], encoded))
        # Blank passwords
        blank_encoded = make_password("", hasher="bcrypt_sha256")
        self.assertTrue(blank_encoded.startswith("bcrypt_sha256$"))
        self.assertTrue(is_password_usable(blank_encoded))
        self.assertTrue(check_password("", blank_encoded))
        self.assertFalse(check_password(" ", blank_encoded))