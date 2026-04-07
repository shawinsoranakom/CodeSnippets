def must_update(self, encoded):
        decoded = self.decode(encoded)
        return must_update_salt(decoded["salt"], self.salt_entropy)