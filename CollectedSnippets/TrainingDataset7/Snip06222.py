def salt(self):
        bcrypt = self._load_library()
        return bcrypt.gensalt(self.rounds)