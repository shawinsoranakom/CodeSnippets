def close(self, **kwargs):
        # Many clients don't clean up connections properly.
        self._cache.disconnect_all()