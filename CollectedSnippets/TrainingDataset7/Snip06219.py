def must_update(self, encoded):
        decoded = self.decode(encoded)
        current_params = decoded["params"]
        new_params = self.params()
        # Set salt_len to the salt_len of the current parameters because salt
        # is explicitly passed to argon2.
        new_params.salt_len = current_params.salt_len
        update_salt = must_update_salt(decoded["salt"], self.salt_entropy)
        return (current_params != new_params) or update_salt