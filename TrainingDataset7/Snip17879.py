def test_bcrypt_salt_check(self):
        hasher = BCryptPasswordHasher()
        encoded = hasher.encode("lètmein", hasher.salt())
        self.assertIs(hasher.must_update(encoded), False)