def verify(self, password, encoded):
        argon2 = self._load_library()
        algorithm, rest = encoded.split("$", 1)
        assert algorithm == self.algorithm
        try:
            return argon2.PasswordHasher().verify("$" + rest, password)
        except argon2.exceptions.VerificationError:
            return False