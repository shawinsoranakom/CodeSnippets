def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        """
        Set a bunch of values in the cache at once from a dict of key/value
        pairs. For certain backends (memcached), this is much more efficient
        than calling set() multiple times.

        If timeout is given, use that timeout for the key; otherwise use the
        default cache timeout.

        On backends that support it, return a list of keys that failed
        insertion, or an empty list if all keys were inserted successfully.
        """
        for key, value in data.items():
            self.set(key, value, timeout=timeout, version=version)
        return []