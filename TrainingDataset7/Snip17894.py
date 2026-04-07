def test_password_and_salt_in_str_and_bytes_bcrypt(self):
        hasher_classes = [
            BCryptPasswordHasher,
            BCryptSHA256PasswordHasher,
        ]
        for hasher_class in hasher_classes:
            hasher = hasher_class()
            with self.subTest(hasher_class.__name__):
                passwords = ["password", b"password"]
                for password in passwords:
                    salts = [hasher.salt().decode(), hasher.salt()]
                    for salt in salts:
                        encoded = hasher.encode(password, salt)
                        for password_to_verify in passwords:
                            self.assertIs(
                                hasher.verify(password_to_verify, encoded), True
                            )