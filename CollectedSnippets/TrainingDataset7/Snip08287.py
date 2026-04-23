def delete(self, key, version=None):
        key = self.make_and_validate_key(key, version=version)
        with self._lock:
            return self._delete(key)