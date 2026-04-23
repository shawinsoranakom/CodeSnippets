def delete(self, session_key=None):
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        try:
            os.unlink(self._key_to_file(session_key))
        except OSError:
            pass