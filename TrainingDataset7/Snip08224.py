def decr(self, key, delta=1, version=None):
        """
        Subtract delta from value in the cache. If the key does not exist,
        raise a ValueError exception.
        """
        return self.incr(key, -delta, version=version)