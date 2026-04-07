def test_encode_invalid_salt(self):
        hasher_classes = [
            MD5PasswordHasher,
            PBKDF2PasswordHasher,
            PBKDF2SHA1PasswordHasher,
            ScryptPasswordHasher,
        ]
        msg = "salt must be provided and cannot contain $."
        for hasher_class in hasher_classes:
            hasher = hasher_class()
            for salt in [None, "", "sea$salt"]:
                with self.subTest(hasher_class.__name__, salt=salt):
                    with self.assertRaisesMessage(ValueError, msg):
                        hasher.encode("password", salt)