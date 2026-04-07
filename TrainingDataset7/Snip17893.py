def test_password_and_salt_in_str_and_bytes_argon2(self):
        hasher = Argon2PasswordHasher()
        passwords = ["password", b"password"]
        for password in passwords:
            for salt in [hasher.salt(), hasher.salt().encode()]:
                encoded = hasher.encode(password, salt)
                for password_to_verify in passwords:
                    self.assertIs(hasher.verify(password_to_verify, encoded), True)