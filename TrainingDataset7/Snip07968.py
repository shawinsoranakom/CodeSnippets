def cache_key(self):
        return self.cache_key_prefix + self._get_or_create_session_key()