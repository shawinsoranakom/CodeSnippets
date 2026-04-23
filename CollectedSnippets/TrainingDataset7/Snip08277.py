def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_and_validate_key(key, version=version)
        pickled = pickle.dumps(value, self.pickle_protocol)
        with self._lock:
            if self._has_expired(key):
                self._set(key, pickled, timeout)
                return True
            return False