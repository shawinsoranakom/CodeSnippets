def save(self, must_create=False):
        super().save(must_create)
        try:
            self._cache.set(self.cache_key, self._session, self.get_expiry_age())
        except Exception:
            logger.exception("Error saving to cache (%s)", self._cache)