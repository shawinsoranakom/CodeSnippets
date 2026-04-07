def _has_expired(self, key):
        exp = self._expire_info.get(key, -1)
        return exp is not None and exp <= time.time()