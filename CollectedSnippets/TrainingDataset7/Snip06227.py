def must_update(self, encoded):
        decoded = self.decode(encoded)
        return decoded["work_factor"] != self.rounds