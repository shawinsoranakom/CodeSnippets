def test_password_and_salt_in_str_and_bytes(self):
        hasher_classes = [
            MD5PasswordHasher,
            PBKDF2PasswordHasher,
            PBKDF2SHA1PasswordHasher,
            ScryptPasswordHasher,
        ]
        for hasher_class in hasher_classes:
            hasher = hasher_class()
            with self.subTest(hasher_class.__name__):
                passwords = ["password", b"password"]
                for password in passwords:
                    for salt in [hasher.salt(), hasher.salt().encode()]:
                        encoded = hasher.encode(password, salt)
                        for password_to_verify in passwords:
                            self.assertIs(
                                hasher.verify(password_to_verify, encoded), True
                            )