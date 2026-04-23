def incr(self, key, delta=1, version=None):
        key = self.make_and_validate_key(key, version=version)
        try:
            # Memcached doesn't support negative delta.
            if delta < 0:
                val = self._cache.decr(key, -delta)
            else:
                val = self._cache.incr(key, delta)
        # Normalize an exception raised by the underlying client library to
        # ValueError in the event of a nonexistent key when calling
        # incr()/decr().
        except self.LibraryValueNotFoundException:
            val = None
        if val is None:
            raise ValueError("Key '%s' not found" % key)
        return val