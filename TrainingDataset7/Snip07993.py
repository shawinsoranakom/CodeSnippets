def flush(self):
        """
        Remove the current session data from the database and regenerate the
        key.
        """
        self.clear()
        self.delete(self.session_key)
        self._session_key = None