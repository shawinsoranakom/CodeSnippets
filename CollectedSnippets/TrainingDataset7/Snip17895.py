def test_encode_password_required(self):
        hasher_classes = [
            MD5PasswordHasher,
            PBKDF2PasswordHasher,
            PBKDF2SHA1PasswordHasher,
            ScryptPasswordHasher,
        ]
        msg = "password must be provided."
        for hasher_class in hasher_classes:
            hasher = hasher_class()
            with self.subTest(hasher_class.__name__):
                with self.assertRaisesMessage(TypeError, msg):
                    hasher.encode(None, "seasalt")