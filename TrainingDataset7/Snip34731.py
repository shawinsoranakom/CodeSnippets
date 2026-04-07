def save(self, must_create=False):
        self._session_key = self.encode(self._session)