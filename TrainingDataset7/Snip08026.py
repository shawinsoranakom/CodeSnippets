def exists(self, session_key):
        return os.path.exists(self._key_to_file(session_key))