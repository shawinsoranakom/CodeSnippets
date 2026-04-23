def load(self):
        try:
            data = self._cache.get(self.cache_key)
        except Exception:
            # Some backends (e.g. memcache) raise an exception on invalid
            # cache keys. If this happens, reset the session. See #17810.
            data = None

        if data is None:
            s = self._get_session_from_db()
            if s:
                data = self.decode(s.session_data)
                self._cache.set(
                    self.cache_key, data, self.get_expiry_age(expiry=s.expire_date)
                )
            else:
                data = {}
        return data