def save(self, must_create=False):
        if self.session_key is None:
            return self.create()
        if must_create:
            func = self._cache.add
        elif self._cache.get(self.cache_key) is not None:
            func = self._cache.set
        else:
            raise UpdateError
        result = func(
            self.cache_key,
            self._get_session(no_load=must_create),
            self.get_expiry_age(),
        )
        if must_create and not result:
            raise CreateError