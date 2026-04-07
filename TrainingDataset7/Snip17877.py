def test_low_level_pbkdf2(self):
        hasher = PBKDF2PasswordHasher()
        encoded = hasher.encode("lètmein", "seasalt2")
        self.assertEqual(
            encoded,
            "pbkdf2_sha256$1500000$"
            "seasalt2$xWKIh704updzhxL+vMfPbhVsHljK62FyE988AtcoHU4=",
        )
        self.assertTrue(hasher.verify("lètmein", encoded))