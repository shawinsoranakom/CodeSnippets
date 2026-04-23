def _delete(self, key):
        try:
            del self._cache[key]
            del self._expire_info[key]
        except KeyError:
            return False
        return True