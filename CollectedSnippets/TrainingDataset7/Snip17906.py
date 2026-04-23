def test_argon2(self):
        encoded = make_password("lètmein", hasher="argon2")
        self.assertTrue(is_password_usable(encoded))
        self.assertTrue(encoded.startswith("argon2$argon2id$"))
        self.assertTrue(check_password("lètmein", encoded))
        self.assertFalse(check_password("lètmeinz", encoded))
        self.assertEqual(identify_hasher(encoded).algorithm, "argon2")
        # Blank passwords
        blank_encoded = make_password("", hasher="argon2")
        self.assertTrue(blank_encoded.startswith("argon2$argon2id$"))
        self.assertTrue(is_password_usable(blank_encoded))
        self.assertTrue(check_password("", blank_encoded))
        self.assertFalse(check_password(" ", blank_encoded))
        # Old hashes without version attribute
        encoded = (
            "argon2$argon2i$m=8,t=1,p=1$c29tZXNhbHQ$gwQOXSNhxiOxPOA0+PY10P9QFO"
            "4NAYysnqRt1GSQLE55m+2GYDt9FEjPMHhP2Cuf0nOEXXMocVrsJAtNSsKyfg"
        )
        self.assertTrue(check_password("secret", encoded))
        self.assertFalse(check_password("wrong", encoded))
        # Old hashes with version attribute.
        encoded = "argon2$argon2i$v=19$m=8,t=1,p=1$c2FsdHNhbHQ$YC9+jJCrQhs5R6db7LlN8Q"
        self.assertIs(check_password("secret", encoded), True)
        self.assertIs(check_password("wrong", encoded), False)
        # Salt entropy check.
        hasher = get_hasher("argon2")
        encoded_weak_salt = make_password("lètmein", "iodizedsalt", "argon2")
        encoded_strong_salt = make_password("lètmein", hasher.salt(), "argon2")
        self.assertIs(hasher.must_update(encoded_weak_salt), True)
        self.assertIs(hasher.must_update(encoded_strong_salt), False)