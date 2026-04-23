def test_bcryptsha256_salt_check(self):
        hasher = BCryptSHA256PasswordHasher()
        encoded = hasher.encode("lètmein", hasher.salt())
        self.assertIs(hasher.must_update(encoded), False)