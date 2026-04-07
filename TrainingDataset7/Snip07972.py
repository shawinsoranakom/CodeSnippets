def create(self):
        # Because a cache can fail silently (e.g. memcache), we don't know if
        # we are failing to create a new session because of a key collision or
        # because the cache is missing. So we try for a (large) number of times
        # and then raise an exception. That's the risk you shoulder if using
        # cache backing.
        for i in range(10000):
            self._session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            return
        raise RuntimeError(
            "Unable to create a new session key. "
            "It is likely that the cache is unavailable."
        )