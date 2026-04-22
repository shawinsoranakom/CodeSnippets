def __init__(self, cache_type: CacheType):
        self._hashes: Dict[Any, bytes] = {}

        # The number of the bytes in the hash.
        self.size = 0

        self.cache_type = cache_type