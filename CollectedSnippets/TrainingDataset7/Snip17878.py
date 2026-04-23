def test_low_level_pbkdf2_sha1(self):
        hasher = PBKDF2SHA1PasswordHasher()
        encoded = hasher.encode("lètmein", "seasalt2")
        self.assertEqual(
            encoded, "pbkdf2_sha1$1500000$seasalt2$ep4Ou2hnt2mlvMRsIjUln0Z5MYY="
        )
        self.assertTrue(hasher.verify("lètmein", encoded))