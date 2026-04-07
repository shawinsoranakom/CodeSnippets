def must_update(self, encoded):
        decoded = self.decode(encoded)
        update_salt = must_update_salt(decoded["salt"], self.salt_entropy)
        return (decoded["iterations"] != self.iterations) or update_salt